#!/usr/bin/env python2
import unittest

from utils import TestUtils, KubeUtils, NVMESH_MGMT_ADDRESSES

logger = TestUtils.get_logger()

@unittest.skipIf(len(NVMESH_MGMT_ADDRESSES) < 2, reason="topology test requires at least 2 NVMesh Clusters forming 2 differenet zones. Check env var NVMESH_MGMT_ADDRESSES")
class TestTopology(unittest.TestCase):
	def _create_first_consumer_storage_class(self):
		# create storage class
		sc_name = 'topology-test-wait-for-consumer'
		KubeUtils.create_storage_class(sc_name, {'vpg': 'DEFAULT_CONCATENATED_VPG'}, volumeBindingMode='WaitForFirstConsumer')
		return sc_name

	def _collect_pods_info(self, pod_names):
		info = {}

		for pod_name in pod_names:
			info[pod_name] = {}

			pod = KubeUtils.get_pod_by_name(pod_name)

			node_name = pod.spec.node_name
			node = KubeUtils.get_node_by_name(node_name)
			zone = KubeUtils.get_zone_from_node(node)

			info[pod_name] = {
				'pod': pod,
				'node_name': node_name,
				'node': node,
				'zone': zone
			}

		return info

	def _check_pods_using_same_pvc_are_on_same_zone(self, storage_class_name):
		pod_names = set()
		for i in range(5):
			pod_names.add('pod-' + str(i))

		# create PVC
		pvc_name = 'topology-single-pvc-' + storage_class_name
		KubeUtils.create_pvc_with_cleanup(self, pvc_name, storage_class_name, volumeMode='Block')

		# Create Pods
		for pod_name in pod_names:
			pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
			KubeUtils.create_pod(pod)

		# cleanup
		def pods_cleanup():
			for pod_name in pod_names:
				KubeUtils.delete_pod(pod_name)

			for pod_name in pod_names:
				KubeUtils.wait_for_pod_to_delete(pod_name)

		self.addCleanup(pods_cleanup)

		for pod_name in pod_names:
			KubeUtils.wait_for_pod_to_be_running(pod_name, attempts=15)

		# collect Pod, Node and Zone data
		info = self._collect_pods_info(pod_names)

		# at least 2 different zones
		all_zones = set()

		for pod_name, pod_info in info.iteritems():
			all_zones.add(pod_info['zone'])

		print('all_zones = %s' % all_zones)
		self.assertEqual(len(all_zones), 1)

	def _check_pods_with_different_pvc_spread_across_zones(self, storage_class_name):
		num_of_pods = 6
		pod_names = set()
		pvc_names = set()

		for i in range(num_of_pods):
			pod_names.add('pod-' + str(i))
			pvc_names.add('pvc-' + str(i))


		# create PVCs
		for pvc_name in pvc_names:
			KubeUtils.create_pvc_with_cleanup(self, pvc_name, storage_class_name, volumeMode='Block')

		# Create Pods
		for i in range(num_of_pods):
			pod_name = 'pod-' + str(i)
			pvc_name = 'pvc-' + str(i)
			pod = KubeUtils.get_block_consumer_pod_template(pod_name, pvc_name)
			KubeUtils.create_pod(pod)

		# pods cleanups
		def cleanup():
			for pod_name in pod_names:
				KubeUtils.delete_pod(pod_name)

			for pod_name in pod_names:
				KubeUtils.wait_for_pod_to_delete(pod_name)

		self.addCleanup(cleanup)

		for pod_name in pod_names:
			KubeUtils.wait_for_pod_to_be_running(pod_name, attempts=30)

		# collect Pod, Node and Zone data
		info = self._collect_pods_info(pod_names)

		# at least 2 different zones
		all_zones = set()

		for pod_name, pod_info in info.iteritems():
			all_zones.add(pod_info['zone'])

		print('all_zones = %s' % all_zones)
		self.assertGreater(len(all_zones), 1)

	def test_pods_spread_immediate(self):
		sc_name = 'nvmesh-concatenated'
		self._check_pods_with_different_pvc_spread_across_zones(sc_name)

	def test_pods_spread_first_consumer(self):
		sc_name = self._create_first_consumer_storage_class()
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))
		self._check_pods_with_different_pvc_spread_across_zones(sc_name)

	def test_pods_sharing_pvc_on_same_zone_immediate(self):
		sc_name = 'nvmesh-concatenated'
		self._check_pods_using_same_pvc_are_on_same_zone(sc_name)

	def test_pods_sharing_pvc_on_same_zone_first_consumer(self):
		sc_name = self._create_first_consumer_storage_class()
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))
		self._check_pods_using_same_pvc_are_on_same_zone(sc_name)

if __name__ == '__main__':
	TestUtils.run_unittest()
