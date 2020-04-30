#!/usr/bin/env python2
import time
import unittest

from utils import TestUtils, KubeUtils, NVMeshUtils

logger = TestUtils.get_logger()

class TestFileSystemVolume(unittest.TestCase):

	def _test_fs_type(self, fs_type):

		# Create Storage class for the specific File System Type
		sc_name = 'raid1-{}'.format(fs_type)
		sc_params = { 'fsType': fs_type, 'vpg': 'DEFAULT_RAID_1_VPG' }
		KubeUtils.create_storage_class(sc_name, sc_params)
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))

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

	def test_ext4(self):
		self._test_fs_type('ext4')

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

	def test_extend_fs_volume(self):
		# Create PVC
		pvc_name = 'pvc-extend-fs'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, 'nvmesh-raid10')

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

		NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, { 'capacity': size_5_gib_in_bytes }, self, attempts=15)

		# check block device size in container (using lsblk)
		KubeUtils.wait_for_block_device_resize(self, pod_name, nvmesh_vol_name, '5G')

		# check file system size inside the container  (using df -h)
		self._wait_for_file_system_resize(pod_name, '4.9G')

	def _wait_for_file_system_resize(self, pod_name, new_size, attempts=30):
		size = None
		while attempts:
			attempts = attempts - 1

			stdout = KubeUtils.run_command_in_container(pod_name, 'df -h /mnt/vol')
			if stdout:
				lines = stdout.split('\n')
				line = lines[2]
				columns = line.split()
				size = columns[0]

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
