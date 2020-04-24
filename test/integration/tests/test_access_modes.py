#!/usr/bin/env python2

import unittest

from utils import TestUtils, KubeUtils, NVMeshUtils

logger = TestUtils.get_logger()


class TestAccessModes(unittest.TestCase):
	StorageClass = 'nvmesh-raid1'

	def test_read_write_many(self):
		pvc_name = 'pvc-rwx'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadWriteMany'], volumeMode='Block')

		# First Pod Should Succeed
		pod1_name = 'pod-1-node-1'
		self._create_pod_on_specific_node(pod1_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod1_name)

		# Second Pod on the same Node should Succeed
		pod2_name = 'pod-2-node-1'
		self._create_pod_on_specific_node(pod2_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod2_name)

		# Third Pod on a different Node should Succeed
		pod3_name = 'pod-3-node-2'
		self._create_pod_on_specific_node(pod3_name, pvc_name, node_index=2)
		KubeUtils.wait_for_pod_to_be_running(pod3_name)

		KubeUtils.delete_pod(pod1_name)
		KubeUtils.delete_pod(pod2_name)
		KubeUtils.delete_pod(pod3_name)

	@unittest.skipIf(NVMeshUtils.get_nvmesh_version_tuple() < (2,1), 'ExclusiveMode not supported before NVMesh 2.1')
	def test_read_write_once(self):
		pvc_name = 'pvc-rwo'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadWriteOnce'], volumeMode='Block')

		# First Pod Should Succeed
		pod1_name = 'pod-1-node-1'
		self._create_pod_on_specific_node(pod1_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod1_name)

		# Second Pod on the same Node should Fail
		pod2_name = 'pod-2-node-1'
		self._create_pod_on_specific_node(pod2_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_fail(pod2_name)

		# Third Pod on a different Node should Fail
		pod3_name = 'pod-3-node-2'
		self._create_pod_on_specific_node(pod3_name, pvc_name, node_index=2)
		KubeUtils.wait_for_pod_to_fail(pod3_name)

		KubeUtils.delete_pod(pod1_name)
		KubeUtils.delete_pod(pod2_name)
		KubeUtils.delete_pod(pod3_name)

	def test_read_only_many(self):
		pvc_name = 'pvc-rom'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadOnlyMany'], volumeMode='Block')

		# First Pod Should Succeed
		pod1_name = 'pod-1-node-1'
		self._create_pod_on_specific_node(pod1_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod1_name)

		# Second Pod on the same Node should Succeed
		pod2_name = 'pod-2-node-1'
		self._create_pod_on_specific_node(pod2_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod2_name)

		# Third Pod on a different Node should Succeed
		pod3_name = 'pod-3-node-2'
		self._create_pod_on_specific_node(pod3_name, pvc_name, node_index=2)
		KubeUtils.wait_for_pod_to_be_running(pod3_name)

		KubeUtils.delete_pod(pod1_name)
		KubeUtils.delete_pod(pod2_name)
		KubeUtils.delete_pod(pod3_name)

	@unittest.skip('Not Implemented')
	def test_mixed_access_modes(self):
		# TODO: Implement
		# 1. Create Storage Class with reclaimPolicy: Retain
		# 2. Create PVC with All Access Modes and VolumeMode FileSystem
		# 3. Create Pod to create a file on the File System
		# 4. Delete the PVC
		# 5. Make PV Available for the next PVC (by removing claimRef field from the PV)
		# 6. Create PVC With ReadOnlyMany
		# 7. Create 2 Pods that will read the File System - Should Succeed
		# 8. Create 1 Pod that will try to write to the FileSystem - Should Fail
		raise NotImplementedError()

	def _create_pod_on_specific_node(self, pod_name, pvc_name, node_index):
		pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
		pod['spec']['nodeSelector'] = { 'worker-index': str(node_index) }
		KubeUtils.create_pod(pod)

		def cleanup_pod(name):
			KubeUtils.delete_pod(name)
			KubeUtils.wait_for_pod_to_delete(name)

		self.addCleanup(lambda: cleanup_pod(pod_name))


if __name__ == '__main__':
	TestUtils.run_unittest()
