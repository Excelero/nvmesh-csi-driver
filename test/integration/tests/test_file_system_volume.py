#!/usr/bin/env python2
import time
import unittest

from driver.consts import FSType
from utils import TestUtils, KubeUtils, NVMeshUtils

logger = TestUtils.get_logger()

class TestFileSystemVolume(unittest.TestCase):

	def _create_storage_class_for_fs_type(self, fs_type, vpg='DEFAULT_RAID_1_VPG'):
		sc_name = 'file-system-volume-{}'.format(fs_type)
		sc_params = {'fsType': fs_type, 'vpg': vpg}
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))
		KubeUtils.create_storage_class(sc_name, sc_params)
		return sc_name

	def _test_fs_type(self, fs_type, **kwargs):
		# Create Storage class for the specific File System Type
		sc_name = self._create_storage_class_for_fs_type(fs_type, **kwargs)

		# create the PVC
		pvc_name = 'test-{}'.format(fs_type)
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name)

		# Create Consumer pod
		pod_name = 'consumer-{}'.format(fs_type)
		pod = KubeUtils.get_fs_consumer_pod_template(pod_name, pvc_name)
		KubeUtils.create_pod(pod)

		def cleanup_pod():
			KubeUtils.delete_pod(pod_name)
			KubeUtils.wait_for_pod_to_delete(pod_name)

		self.addCleanup(cleanup_pod)

		KubeUtils.wait_for_pod_to_be_running(pod_name)

	def test_ext4_concatenated(self):
		self._test_fs_type('ext4', vpg='DEFAULT_CONCATENATED_VPG')

	def test_ext4(self):
		self._test_fs_type('ext4')

	def test_xfs_concatenated(self):
		self._test_fs_type('xfs', vpg='DEFAULT_CONCATENATED_VPG')

	def test_xfs(self):
		self._test_fs_type('xfs')

	def test_file_system_persistency(self):
		# create the PVC
		pvc_name = 'pvc-fs-persistency-test'
		sc_name = 'nvmesh-raid10'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name)

		data_to_write = "Persistency Test"

		# Create pod to write a file in the FS
		self._run_shell_pod('job-writer', pvc_name, "echo '{}' > /vol/file1".format(data_to_write))

		# Create pod to read the file content
		pod_reader_name = 'job-reader'
		self._run_shell_pod(pod_reader_name, pvc_name, "cat /vol/file1")

		# get logs and verify output
		pod_log = KubeUtils.get_pod_log(pod_reader_name)
		self.assertEqual(pod_log.strip(), data_to_write)

	def _test_extend_fs_volume(self, storage_class_name, fs_type):
		# Create PVC
		pvc_name = 'pvc-extend-fs'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, storage_class_name, access_modes=['ReadWriteMany'])

		# Create Pod
		pod_name = 'extend-fs-consumer'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_name, pvc_name)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))
		KubeUtils.wait_for_pod_to_be_running(pod_name)

		# Edit the PVC to increase the volume capacity
		new_size = '5Gi'
		pvc_patch = {
			'spec': {
				'resources': {
					'requests': {
						'storage': new_size
					}
				},
			}
		}

		logger.info("Extending Volume {}".format(pvc_name))
		KubeUtils.patch_pvc(pvc_name, pvc_patch)

		# verify kuberentes object updated
		KubeUtils.wait_for_pvc_to_extend(pvc_name, new_size)

		# wait for NVMesh Volume to show the updated size
		nvmesh_vol_name = KubeUtils.get_nvmesh_vol_name_from_pvc_name(pvc_name)
		size_5_gib_in_bytes = 5368709120

		NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, {'capacity': size_5_gib_in_bytes}, self, attempts=15)

		# check block device size in container (using lsblk)
		KubeUtils.wait_for_block_device_resize(self, pod_name, nvmesh_vol_name, '5G')

		# check file system size inside the container  (using df -h)
		expected_size = '4.9G' if fs_type == FSType.EXT4 else '5.0G'
		self._wait_for_file_system_resize(pod_name, expected_size)

	def test_extend_file_system_ext4(self):
		fs_type = FSType.EXT4
		sc_name = self._create_storage_class_for_fs_type(fs_type, vpg='DEFAULT_CONCATENATED_VPG')
		self._test_extend_fs_volume(storage_class_name=sc_name, fs_type=fs_type)

	def test_extend_file_system_xfs(self):
		fs_type = FSType.XFS
		sc_name = self._create_storage_class_for_fs_type(fs_type, vpg='DEFAULT_CONCATENATED_VPG')
		self._test_extend_fs_volume(storage_class_name=sc_name, fs_type=fs_type)

	def _wait_for_file_system_resize(self, pod_name, new_size, attempts=30):
		size = None
		while attempts:
			attempts = attempts - 1

			stdout = KubeUtils.run_command_in_container(pod_name, ['df', '-h', '--output=size', '/mnt/vol'])
			if stdout:
				lines = stdout.strip().split('\n')
				line = lines[-1]
				size = line.strip()

				if size == new_size:
					# success
					logger.info('File System on {} was extended to {}'.format(pod_name, new_size))
					return
				else:
					logger.debug('Waiting for file system to extend to {} current size is {}'.format(new_size, size))

			time.sleep(1)

		self.assertEqual(size, new_size, 'Timed out waiting for File System to resize')

	def _run_shell_pod(self, pod_name, pvc_name, cmd, attempts=60):
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_complete(pod_name, attempts=attempts)

if __name__ == '__main__':
	TestUtils.run_unittest()
