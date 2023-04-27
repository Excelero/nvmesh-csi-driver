#!/usr/bin/env python2
import time
import unittest

from utils import TestUtils, KubeUtils, NVMeshUtils, TestConfig

logger = TestUtils.get_logger().getChild("TestEncryptedVolumes")

class TestEncryptedVolumes(unittest.TestCase):

	def test_dmcrypt_volume_with_xfs(self):
		logger.getChild("test_dmcrypt_volume_with_xfs")
		logger.info("Started")
	
		key_secret_name = 'dmcrypt-example-key'
	
		logger.info("create secret")

		dmcrypt_key_secret = {
			'apiVersion': 'v1',
			'kind': 'Secret',
			'metadata': {
				'name': key_secret_name,
			},
			'data': {
				# echo "my-dm-crypt-key\n" | base64
				'dmcryptKey': 'bXktZG0tY3J5cHQta2V5Cg=='
			}
		}
	
		self.addCleanup(lambda: KubeUtils.delete_secret(key_secret_name))
		KubeUtils.create_secret(dmcrypt_key_secret)

		logger.info("Create StorageClass")

		sc_name = 'encrypted-xfs'
		sc_params = {
			'vpg': 'DEFAULT_CONCATENATED_VPG',
			'fsType': 'xfs',
			'encryption': 'dmcrypt',
			'dmcrypt/type': 'luks2',
			'dmcrypt/cipher': 'aes-xts-plain64',
			'csi.storage.k8s.io/node-stage-secret-name': key_secret_name,
			'csi.storage.k8s.io/node-stage-secret-namespace': TestConfig.TestNamespace
		}
	
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))
		KubeUtils.create_storage_class(sc_name, sc_params)
	
		# create the PVC
		pvc_name = 'encrypted-xfs-pvc'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name)
	
		# Create 2 Pods
		pod_name = 'pod-using-encrypted-vol-1'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_name, pvc_name, privileged=True)

		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		logger.info("Waiting for pod to be running")
		KubeUtils.wait_for_pod_to_be_running(pod_name)

		## TEST EXTEND
		logger.info("Testing volume extend expect block device, dmcrypt device and filesystem to reflect new size")

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

		logger.info("wait for NVMesh Volume to show the updated size")

		nvmesh_vol_name = KubeUtils.get_nvmesh_vol_name_from_pvc_name(pvc_name)
		size_5_gib_in_bytes = 5368709120

		NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, {'capacity': size_5_gib_in_bytes}, self, attempts=15)

		# check block device size in container (using lsblk)
		logger.info("verfiy block device resized inside the container")
		KubeUtils.wait_for_block_device_resize(self, pod_name, nvmesh_vol_name, '5G')

		# check file system size inside the container (using df -h)
		# NOTE: the NodeExpandVolume seem to come in a significant delay (1 minute)
		# after the ControllerExpandVolume returned its response

		# check dmcrypt device size in container (using lsblk)
		logger.info("check dmcrypt device size in container")
		KubeUtils.wait_for_block_device_resize(self, pod_name, 'crypt /mnt/vol', '5G', attempts=120)

		logger.info("check xfs filesystem is resized in container")
		expected_size = '5.0G'
		self._wait_for_file_system_resize(pod_name, expected_size, attempts=30)

		KubeUtils.delete_pod_and_wait(pod_name)

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

	def test_dmcrypt_volume_as_block_device(self):
		logger.getChild("test_dmcrypt_volume_as_block_device")
		logger.info("Started")
	
		key_secret_name = 'dmcrypt-example-key'

		# create secret
		dmcrypt_key_secret = {
			'apiVersion': 'v1',
			'kind': 'Secret',
			'metadata': {
				'name': key_secret_name,
			},
			'data': {
				# echo "my-dm-crypt-key\n" | base64
				'dmcryptKey': 'bXktZG0tY3J5cHQta2V5Cg=='
			}
		}

		self.addCleanup(lambda: KubeUtils.delete_secret(key_secret_name))
		KubeUtils.create_secret(dmcrypt_key_secret)

		# Create StorageClass
		sc_name = 'encrypted-block'
		sc_params = {
			'vpg': 'DEFAULT_CONCATENATED_VPG',
			#'encryption': 'dmcrypt',
			'dmcrypt/type': 'luks2',
			'dmcrypt/cipher': 'aes-xts-plain64',
			'csi.storage.k8s.io/node-stage-secret-name': key_secret_name,
			'csi.storage.k8s.io/node-stage-secret-namespace': TestConfig.TestNamespace
		}

		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))
		KubeUtils.create_storage_class(sc_name, sc_params)

		# create the PVC
		pvc_name = 'encrypted-block-pvc'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name, volumeMode='Block')

		# Create 2 Pods
		logger.info("Creating 2 Pods")
		pod_name = 'pod-using-encrypted-vol-1'
		pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name, privileged=True)

		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_be_running(pod_name)

		self._test_extend_dmcrypt_as_block(pvc_name, pod_name)

		KubeUtils.delete_pod_and_wait(pod_name)

	def _run_shell_pod(self, pod_name, pvc_name, cmd, attempts=60):
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_complete(pod_name, attempts=attempts)

	def _test_extend_dmcrypt_as_block(self, pvc_name, pod1_name):
		## TEST EXTEND
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
		KubeUtils.wait_for_block_device_resize(self, pod1_name, nvmesh_vol_name, '5G')

		# check dmcrypt device size in container (using lsblk)
		# TODO: we currently can't see the crypt partition in the container by either running lsblk or simply ls-l /dev/mapper, even with priviliged flag and /dev/ mounted
		#KubeUtils.wait_for_block_device_resize(self, pod1_name, 'crypt /mnt/vol', '5G', attempts=120)

if __name__ == '__main__':
	TestUtils.run_unittest()
