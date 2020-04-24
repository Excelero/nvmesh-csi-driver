#!/usr/bin/env python2

import time
import unittest

import test_utils
from test.integration.tests.test_utils import get_nvmesh_vol_name_from_pvc_name
from test_utils import TestUtils, KubeUtils, NVMeshUtils

core_api = test_utils.core_api
storage_api = test_utils.storage_api

logger = TestUtils.get_logger()
namespace = TestUtils.get_test_namespace()

class TestAttachDetachExtend(unittest.TestCase):
	def test_step_1_create_volumes(self):
		storage_class = 'nvmesh-raid1'
		num_of_volumes = test_utils.TestConfig.NumberOfVolumes
		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			pvc = KubeUtils.get_pvc_template(pvc_name, storage_class)
			logger.info("Creating PVC {}".format(pvc_name))
			KubeUtils.create_pvc(pvc)

		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.wait_for_pvc_to_bound(pvc_name)

	def test_step_2_create_consumer_pods(self):
		for i in range(test_utils.TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			spec = {
				'containers': [
					{
						'name': 'fs-consumer',
						'image': 'excelero/fs-consumer-test:develop',
						'volumeMounts': [
							{
								'name': 'fs-volume',
								'mountPath': '/mnt/vol'
							}
						]
					}
				],
				'volumes': [
					{
						'name': 'fs-volume',
						'persistentVolumeClaim': {
							'claimName': 'vol-{}'.format(i)
						}
					}
				]
			}
			pod = KubeUtils.get_pod_template(pod_name, spec)
			logger.info("Creating Pod {}".format(pod_name))
			KubeUtils.create_pod(pod)

	def test_step_3_extend_volumes(self):
		for i in range(test_utils.TestConfig.NumberOfVolumes):
			pvc_name = 'vol-{}'.format(i)
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

			# edit the pvc
			logger.info("Extending Volume {}".format(pvc_name))
			KubeUtils.patch_pvc(pvc_name, pvc_patch)

			# verify kuberentes object updated
			KubeUtils.wait_for_pvc_to_extend(pvc_name, new_size)

			# wait for NVMesh Volume to show the updated size
			nvmesh_vol_name = get_nvmesh_vol_name_from_pvc_name(pvc_name)
			size_5_gib_in_bytes = 5368709120

			NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, { 'capacity': size_5_gib_in_bytes }, self, attempts=15)


			pod_name = 'consumer-{}'.format(i)

			# check block device size in container (using lsblk)
			self._wait_for_block_device_resize(pod_name, nvmesh_vol_name, '5G')

			# check file system size inside the container  (using df -h)
			self._wait_for_file_system_resize(pod_name, nvmesh_vol_name, '4.9G')

	def _wait_for_block_device_resize(self, pod_name, nvmesh_vol_name, new_size, attempts=30):
		size = None

		while attempts:
			attempts = attempts - 1
			# check block device size in container
			stdout = KubeUtils.run_command_in_container(pod_name, 'lsblk')
			if stdout:
				lines = stdout.split('\n')
				for line in lines:
					if nvmesh_vol_name in line:
						columns = line.split()
						size = columns[3]
						break
			if size == new_size:
				# success
				logger.info('Block device on {} was extended to {}'.format(pod_name, new_size))
				return
			else:
				logger.debug('Waiting for block device to extend to {} current size is {}'.format(new_size, size))

			time.sleep(1)

		self.assertEqual(size, new_size, 'Timed out waiting for Block Device to resize')

	def _wait_for_file_system_resize(self, pod_name, nvmesh_vol_name, new_size, attempts=30):
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

	def test_step_4_delete_pods(self):
		for i in range(test_utils.TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.delete_pod(pod_name)
			KubeUtils.wait_for_pod_to_delete(pod_name)

	def test_step_5_delete_volumes(self):
		for i in range(test_utils.TestConfig.NumberOfVolumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.delete_pvc(pvc_name)
			KubeUtils.wait_for_pvc_to_delete(pvc_name)

if __name__ == '__main__':
	TestUtils.run_unittest()