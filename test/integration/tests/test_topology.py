#!/usr/bin/env python2
import unittest

from utils import TestUtils, KubeUtils, TestConfig, VolumeBindingMode

PARAMS_CONCATENATED_VPG = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

logger = TestUtils.get_logger()


@unittest.skipIf(TestConfig.SkipTopology, "Skipping Topology Tests")
class TestTopology(unittest.TestCase):
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

	def _create_multiple_pods_each_with_own_pvc(self, storage_class_name, num_of_pods=6):
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

		return pod_names

	def _check_pods_with_different_pvc_spread_across_zones(self, storage_class_name):
		pod_names = self._create_multiple_pods_each_with_own_pvc(storage_class_name, num_of_pods=6)

		# collect Pod, Node and Zone data
		info = self._collect_pods_info(pod_names)

		# at least 2 different zones
		all_zones = set()

		for pod_name, pod_info in info.iteritems():
			all_zones.add(pod_info['zone'])

		print('all_zones = %s' % all_zones)
		self.assertGreater(len(all_zones), 1)

	def make_sure_pods_in_correct_zone(self, allowed_zones, info):
		# Make sure all pods created with the correct zone and on one fo the zone nodes
		for pod_name, pod_info in info.iteritems():
			pod_zone = pod_info['zone']
			pod_node_name = pod_info['node_name']
			# Make sure all pods created with one of the allowed zones
			self.assertIn(pod_zone, allowed_zones)

			# Make sure pod node belongs to the zone
			allowed_nodes_per_zone = TestConfig.Topology['zones'][pod_zone]['nodes']
			self.assertIn(pod_node_name, allowed_nodes_per_zone)

	def build_allowed_topologies(self, allowed_zones):
		return [
			{
				'matchLabelExpressions': [
					{
						'key': 'nvmesh-csi.excelero.com/zone',
						'values': allowed_zones
					}
				]
			}
		]

	def _test_single_allowed_topology(self, volumeBindingMode):
		storage_class_name = 'sc-test-allowed-topologies'
		zone_name = TestConfig.Topology['zones'].keys()[0]
		allowed_zones = [zone_name]
		allowedTopologies = self.build_allowed_topologies(allowed_zones)

		KubeUtils.create_storage_class_with_cleanup(
			self,
			storage_class_name,
			PARAMS_CONCATENATED_VPG,
			volumeBindingMode=volumeBindingMode,
			allowedTopologies=allowedTopologies)

		pod_names = self._create_multiple_pods_each_with_own_pvc(storage_class_name, num_of_pods=6)

		# collect Pod, Node and Zone data
		info = self._collect_pods_info(pod_names)

		self.make_sure_pods_in_correct_zone(allowed_zones, info)

	def test_pods_spread_immediate(self):
		sc_name = 'nvmesh-concatenated'
		self._check_pods_with_different_pvc_spread_across_zones(sc_name)

	def test_pods_sharing_pvc_on_same_zone_immediate(self):
		sc_name = 'nvmesh-concatenated'
		self._check_pods_using_same_pvc_are_on_same_zone(sc_name)

	def test_pods_sharing_pvc_on_same_zone_first_consumer(self):
		sc_name = 'test-pods-sharing-zone'
		KubeUtils.create_storage_class_with_cleanup(
			self,
			sc_name,
			PARAMS_CONCATENATED_VPG,
			volumeBindingMode=VolumeBindingMode.Immediate)

		self._check_pods_using_same_pvc_are_on_same_zone(sc_name)

	def test_single_allowed_topology_immediate(self):
		self._test_single_allowed_topology(VolumeBindingMode.Immediate)

	def test_single_allowed_topology_first_consumer(self):
		self._test_single_allowed_topology(VolumeBindingMode.WaitForFirstConsumer)

	def test_multiple_allowed_topologies_immediate(self):
		pods_info, allowed_zones = self._test_storage_class_with_multiple_allowed_topologies(VolumeBindingMode.Immediate)
		used_zones = set([pod['zone'] for pod in pods_info.values()])
		# Make sure both zones were used
		self.assertGreater(len(used_zones), 1)

	def test_multiple_allowed_topologies_first_consumer(self):
		pods_info, allowed_zones = self._test_storage_class_with_multiple_allowed_topologies(VolumeBindingMode.WaitForFirstConsumer)

	def _test_storage_class_with_multiple_allowed_topologies(self, volumeBindingMode):
		storage_class_name = 'sc-test-allowed-topologies'
		# use only 2 first zones
		zone_a = TestConfig.Topology['zones'].keys()[0]
		zone_b = TestConfig.Topology['zones'].keys()[1]
		allowed_zones = [zone_a, zone_b]
		allowedTopologies = self.build_allowed_topologies(allowed_zones)

		KubeUtils.create_storage_class_with_cleanup(
			self,
			storage_class_name,
			PARAMS_CONCATENATED_VPG,
			volumeBindingMode=volumeBindingMode,
			allowedTopologies=allowedTopologies)

		pod_names = self._create_multiple_pods_each_with_own_pvc(storage_class_name, num_of_pods=6)

		# collect Pod, Node and Zone data
		pods_info = self._collect_pods_info(pod_names)

		self.make_sure_pods_in_correct_zone(allowed_zones, pods_info)
		return pods_info, allowed_zones


if __name__ == '__main__':
	TestUtils.run_unittest()
