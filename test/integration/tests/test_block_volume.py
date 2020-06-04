#!/usr/bin/env python2
import unittest

from utils import TestUtils, KubeUtils, NVMeshUtils

logger = TestUtils.get_logger()

class TestBlockVolume(unittest.TestCase):

	def test_block_volume(self):

		# create the PVC
		pvc_name = 'test-block-volume'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, 'nvmesh-raid10', volumeMode='Block')

		# Create Consumer pod
		pod_name = 'block-volume-consumer'
		pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
		KubeUtils.create_pod(pod)
		KubeUtils.wait_for_pod_to_be_running(pod_name)

		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

	def test_block_volume_extend(self):
		# Create PVC
		pvc_name = 'pvc-extend-block'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, 'nvmesh-raid10', volumeMode='Block', access_modes=['ReadWriteMany'])

		# Create Pod
		pod_name = 'extend-block-consumer'
		pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
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

if __name__ == '__main__':
	TestUtils.run_unittest()
