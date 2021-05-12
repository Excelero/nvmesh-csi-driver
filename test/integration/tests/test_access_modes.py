#!/usr/bin/env python2

import unittest

from kubernetes.client.rest import ApiException

from NVMeshSDK.Consts import RAIDLevels
from NVMeshSDK.Entities.Volume import Volume
from utils import TestUtils, KubeUtils, NVMeshUtils, core_api

logger = TestUtils.get_logger()

GiB = pow(1024, 3)

class TestAccessModes(unittest.TestCase):
	StorageClass = 'nvmesh-raid1'
	node_to_zone_map = None
	used_zone = None
	used_nodes = None

	@classmethod
	def setUpClass(cls):
		zones = KubeUtils.get_all_node_names_by_zone()
		TestAccessModes.node_to_zone_map = zones

		for zone, nodes in zones.iteritems():
			if len(nodes) > 1:
				print('Picked zone {} zone with {} nodes: {}'.format(zone, len(nodes), nodes))
				TestAccessModes.used_zone = zone
				TestAccessModes.used_nodes = nodes
				break

			if not TestAccessModes.used_zone:
				raise ValueError('Test requires at least one zone with more than one node. found topology: %s' % zones)

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

	def test_read_write_once(self):
		pvc_name = 'pvc-rwo'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadWriteOnce'], volumeMode='Block')

		# First Pod Should Succeed
		pod1_name = 'pod-1-node-1'
		self._create_pod_on_specific_node(pod1_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod1_name)

		# Second Pod on the same Node - should be running
		pod2_name = 'pod-2-node-1'
		self._create_pod_on_specific_node(pod2_name, pvc_name, node_index=1)
		KubeUtils.wait_for_pod_to_be_running(pod2_name)
		#KubeUtils.wait_for_pod_to_fail(pod2_name)

		# Third Pod on a different Node should Fail
		pod3_name = 'pod-3-node-2'
		self._create_pod_on_specific_node(pod3_name, pvc_name, node_index=2)
		KubeUtils.wait_for_pod_to_fail(pod3_name)

		KubeUtils.delete_pod(pod1_name)
		KubeUtils.delete_pod(pod2_name)
		KubeUtils.delete_pod(pod3_name)

	def test_read_only_many(self):
		pvc_name = 'pvc-rox'
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

	def test_mixed_access_modes(self):
		# This test creates a PV with reclaimPolicy: Retain (making sure it is not deleted when the bounded PVC is deleted)
		# Then will create PVC's with different AccessModes to use the same PV. in between some PV clean needs to be done.
		# Create Storage Class with reclaimPolicy: Retain
		sc_name = 'sc-nvmesh-retain'
		KubeUtils.create_storage_class(sc_name, {'vpg': 'DEFAULT_RAID_10_VPG'}, reclaimPolicy='Retain')
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))

		# Create NVMesh Volume
		nvmesh_volume_name = "test-mixed-access-modes"
		volume = Volume(name=nvmesh_volume_name,
						RAIDLevel=RAIDLevels.STRIPED_AND_MIRRORED_RAID_10,
						VPG='DEFAULT_RAID_10_VPG',
						capacity=5 * GiB,
						description="Volume for CSI Driver Static Provisioning"
						)
		err, out = NVMeshUtils.getVolumeAPI().save([volume])
		self.assertIsNone(err, 'Error Creating NVMesh Volume. %s' % err)
		create_res = out[0]
		self.assertTrue(create_res['success'], 'Error Creating NVMesh Volume. %s' % create_res['error'])

		self.addCleanup(lambda: NVMeshUtils.getVolumeAPI().delete([volume]))

		# Create PV
		pv_name = 'csi-testing-pv-vol1'
		volume_size = '5Gi'

		self.create_pv_for_static_prov(nvmesh_volume_name, pv_name, sc_name, volume_size)

		# Create PVC with accessMode ReadWriteOnce
		pvc_name = 'pvc-rwo'
		KubeUtils.create_pvc_and_wait_to_bound(self,
											   pvc_name,
											   sc_name,
											   access_modes=['ReadWriteOnce'],
											   storage=volume_size,
											   volumeMode='Filesystem')

		self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_name))

		# Create Pod to create a file on the File System
		pod_name = 'pod-file-writer'
		cmd = 'echo hello > /vol/file1'
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_complete(pod_name)
		KubeUtils.delete_pod_and_wait(pod_name)

		# Delete the PVC
		KubeUtils.delete_pvc(pvc_name)
		KubeUtils.wait_for_pv_to_be_released(pv_name)

		# Make PV Available for the next PVC (by removing claimRef field from the PV ==OR== deleting and recreating the PV)
		KubeUtils.delete_pv(pv_name)
		KubeUtils.wait_for_pv_to_delete(pv_name)
		self.create_pv_for_static_prov(nvmesh_volume_name, pv_name, sc_name, volume_size)

		# Create PVC With ReadOnlyMany
		pvc_name = 'pvc-rox'
		KubeUtils.create_pvc_and_wait_to_bound(self,
											   pvc_name,
											   sc_name,
											   access_modes=['ReadOnlyMany'],
											   storage=volume_size,
											   volumeMode='Filesystem')

		self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_name))

		# 7. Create 2 Pods that will read the File System - Should Succeed
		pod1_name = 'pod-file-reader1'
		cmd = 'cat /vol/file1'
		pod = KubeUtils.get_shell_pod_template(pod1_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod1_name))

		pod2_name = 'pod-file-reader2'
		pod = KubeUtils.get_shell_pod_template(pod2_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod2_name))

		KubeUtils.wait_for_pod_to_complete(pod2_name)

		# 8. Create 1 Pod that will try to write to the FileSystem - Should Fail
		pod_name = 'pod-file-writer'
		cmd = 'echo hello > /vol/file1'
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_name, cmd)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_fail(pod_name)

	def create_pv_for_static_prov(self, nvmesh_volume_name, pv_name, sc_name, volume_size):
		all_access_modes = ['ReadWriteOnce', 'ReadOnlyMany', 'ReadWriteMany']
		pv = KubeUtils.get_pv_for_static_provisioning(pv_name=pv_name,
													  nvmesh_volume_name=nvmesh_volume_name,
													  accessModes=all_access_modes,
													  sc_name=sc_name,
													  volume_size=volume_size,
													  volumeMode='Filesystem')
		core_api.create_persistent_volume(pv)

		def pv_cleanup(pv_name):
			try:
				KubeUtils.delete_pv(pv_name)
			except ApiException:
				pass

		self.addCleanup(lambda: pv_cleanup(pv_name))
		pv_list = core_api.list_persistent_volume(field_selector='metadata.name={}'.format(pv_name))
		self.assertIsNotNone(pv_list)
		self.assertTrue(len(pv_list.items))
		self.assertEqual(pv_list.items[0].metadata.name, pv_name)
		return volume_size

	def _create_pod_on_specific_node(self, pod_name, pvc_name, node_index=1):
		pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
		pod['spec']['nodeName'] = TestAccessModes.used_nodes[node_index - 1]
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))


if __name__ == '__main__':
	TestUtils.run_unittest()
