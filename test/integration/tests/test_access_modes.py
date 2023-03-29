#!/usr/bin/env python2
import time
import unittest

from kubernetes.client.rest import ApiException

from NVMeshSDK.Consts import RAIDLevels
from NVMeshSDK.Entities.Volume import Volume
from utils import TestUtils, KubeUtils, NVMeshUtils, core_api

logger = TestUtils.get_logger().getChild("TestAccessModes")

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
		logger.getChild("test_read_write_many")
		logger.info("Started")

		pvc_name = 'pvc-rwx'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadWriteMany'], volumeMode='Block')

		logger.info("First Pod Should Succeed")
		pod = KubeUtils.get_block_consumer_pod_template('pod-1-node-1', pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

		logger.info("Second Pod on the same Node should Succeed")
		pod = KubeUtils.get_block_consumer_pod_template('pod-2-node-1', pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

		logger.info("Third Pod on a different Node should Succeed")
		pod = KubeUtils.get_block_consumer_pod_template('pod-3-node-2', pvc_name)
		self.set_pod_node(pod, node_index=2)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

	def test_read_write_once(self):
		logger.getChild("test_read_write_once")
		logger.info("Started")

		pvc_name = 'pvc-rwo'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadWriteOnce'], volumeMode='Filesystem')

		# First Pod Should Succeed
		logger.info("First Pod Should Succeed")
		pod_1_node_1 = 'pod-1-node-1'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_1_node_1, pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod_1_node_1)

		# Second Pod on the same Node - should be running
		pod_2_node_1 = 'pod-2-node-1'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_2_node_1, pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod_2_node_1)

		# Third Pod on a different Node should Fail
		pod_3_node_2 = 'pod-3-node-2'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_3_node_2, pvc_name)
		self.set_pod_node(pod, node_index=2)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_event(pod_3_node_2, keyword='access mode denied', attempts=20)

		# Delete all pods
		KubeUtils.delete_pods_and_wait([pod_1_node_1, pod_2_node_1], attempts=60)

		# Not waiting now for the failing pod as it would probably take time to shut down
		KubeUtils.delete_pod(pod_3_node_2)
		KubeUtils.delete_pods_and_wait([pod_3_node_2], attempts=120)

		# Forth Pod on Node1 - should be running
		# This should trigger reservation outdated - and then CSI Driver should retry attach with the updated version
		pod_4_node_1 = 'pod-4-node-1'
		pod = KubeUtils.get_fs_consumer_pod_template(pod_4_node_1, pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod_4_node_1)

		KubeUtils.wait_for_pod_to_delete(pod_3_node_2, attempts=60)


	def test_read_only_many_can_read_from_different_pods_and_nodes(self):
		logger.getChild("test_read_only_many_can_read_from_different_pods_and_nodes")
		logger.info("Started")
	
		pvc_name = 'pvc-rox'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, TestAccessModes.StorageClass, access_modes=['ReadOnlyMany'], volumeMode='Block')

		# First Pod Should Succeed
		pod = KubeUtils.get_block_consumer_pod_template('pod-1-node-1', pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

		# Second Pod on the same Node should Succeed
		pod = KubeUtils.get_block_consumer_pod_template('pod-2-node-1', pvc_name)
		self.set_pod_node(pod, node_index=1)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

		# Third Pod on a different Node should Succeed
		pod = KubeUtils.get_block_consumer_pod_template('pod-3-node-2', pvc_name)
		self.set_pod_node(pod, node_index=2)
		self.create_pod_with_cleanup(pod)
		KubeUtils.wait_for_pod_to_be_running(pod['metadata']['name'])

	@unittest.skip("test_mixed_access_modes")
	def test_mixed_access_modes(self):
		logger.getChild("test_mixed_access_modes")
		logger.info("Started")
	
		# This test creates a static provisioned PV with reclaimPolicy: Retain (making sure it is not deleted when the bounded PVC is deleted)
		# Then will create PVC's with different AccessModes to use the same PV. in between some PV cleanup needs to be done.
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
		self.assertTrue(create_res['success'], 'Error Creating NVMesh Volume. %s' % create_res)

		self.addCleanup(lambda: NVMeshUtils.getVolumeAPI().delete([volume]))

		# Create PV
		pv_name = 'csi-testing-pv-vol1'
		volume_size = '5Gi'

		self.create_pv_for_static_prov(nvmesh_volume_name, pv_name, sc_name, volume_size)

		# Create PVC with accessMode ReadWriteOnce
		pvc_rwo = 'pvc-rwo'
		KubeUtils.create_pvc_and_wait_to_bound(self,
											   pvc_rwo,
											   sc_name,
											   access_modes=['ReadWriteOnce'],
											   storage=volume_size,
											   volumeMode='Filesystem')

		self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_rwo))

		# Create Pod to create a file on the File System
		pod_name = 'pod-file-writer-a'
		cmd_write_success = 'echo hello_from_%s > /vol/file1 ; success=$? ; echo "write to file returned $success" ;echo $(cat /vol/file1) ; exit $success' % pod_name
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_rwo, cmd_write_success)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_complete(pod_name)
		KubeUtils.delete_pod_and_wait(pod_name)

		# Delete the PVC
		KubeUtils.delete_pvc(pvc_rwo)
		KubeUtils.wait_for_pv_status(pv_name, expected_statuses=['Released'])

		# Make PV Available for the next PVC (by removing claimRef field from the PV ==OR== deleting and recreating the PV)
		KubeUtils.delete_pv(pv_name)
		KubeUtils.wait_for_pv_to_delete(pv_name)
		self.create_pv_for_static_prov(nvmesh_volume_name, pv_name, sc_name, volume_size)

		# Create PVC With ReadOnlyMany
		pvc_rox = 'pvc-rox'
		KubeUtils.create_pvc_and_wait_to_bound(self,
											   pvc_rox,
											   sc_name,
											   access_modes=['ReadOnlyMany'],
											   storage=volume_size,
											   volumeMode='Filesystem')

		self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_rox))

		# 7. Create 2 Pods that will read the File System - Should Succeed
		pod1_name = 'pod-file-reader1'
		cmd_read_success = 'cat /vol/file1 ; exit $?'
		pod = KubeUtils.get_shell_pod_template(pod1_name, pvc_rox, cmd_read_success)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod1_name))

		pod2_name = 'pod-file-reader2'
		pod = KubeUtils.get_shell_pod_template(pod2_name, pvc_rox, cmd_read_success)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod2_name))

		KubeUtils.wait_for_pod_to_complete(pod2_name)

		# 8. Create 1 Pod that will try to write to the FileSystem - Should Fail
		pod_name = 'pod-file-writer-b'
		cmd_write_success = 'echo hello_from_%s > /vol/file1 ; success=$? ; echo "write to file returned $success" ;echo $(cat /vol/file1) ; while true; do sleep 1; done ;exit $success' % pod_name
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_rox, cmd_write_success)
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod_name))

		KubeUtils.wait_for_pod_to_fail(pod_name, attempts=30)

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

	def set_pod_node(self, pod, node_index=1):
		pod['spec']['nodeName'] = TestAccessModes.used_nodes[node_index - 1]

	def create_pod_with_cleanup(self, pod):
		KubeUtils.create_pod(pod)
		self.addCleanup(lambda: KubeUtils.delete_pod_and_wait(pod['metadata']['name']))

if __name__ == '__main__':
	TestUtils.run_unittest()
