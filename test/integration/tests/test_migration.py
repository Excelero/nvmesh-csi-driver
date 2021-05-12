#!/usr/bin/env python2
import time
import unittest

from utils import TestUtils, KubeUtils, NVMeshUtils, core_api, apps_api

logger = TestUtils.get_logger()

class TestMigration(unittest.TestCase):

	def test_migration(self):
		# create the PVC
		pvc_name = 'pvc-migration-test'
		sc_name = 'nvmesh-raid10'
		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name)

		# Create Deployment
		dep_name = 'test-pod-migration'
		pod = KubeUtils.get_fs_consumer_pod_template(dep_name, pvc_name)
		deployment = KubeUtils.get_deployment_template(dep_name, pod['spec'])
		KubeUtils.create_deployment(deployment)
		self.addCleanup(lambda: KubeUtils.delete_deployment(dep_name))

		attempts = 10
		pod = None
		while attempts:
			logger.debug('Waiting for deployment pods to be scheduled')
			pod_list = KubeUtils.get_pods_for_deployment(dep_name)
			if len(pod_list):
				pod = pod_list[0]
				break

			attempts = attempts - 1
			self.assertNotEqual(attempts, 0, 'Timed out waiting for deployment pod to be scheduled')
			time.sleep(1)

		initial_pod_name = pod.metadata.name
		# Set node as NoSchedule
		initial_node = pod.spec.node_name
		KubeUtils.node_prevent_schedule(initial_node)
		self.addCleanup(lambda: KubeUtils.node_allow_schedule(initial_node))

		# Delete the pod (it is expected to be re-created on a different node
		KubeUtils.delete_pod(initial_pod_name)
		KubeUtils.wait_for_pod_to_delete(initial_pod_name)

		# Get the second Pod
		pods = KubeUtils.get_pods_for_deployment(dep_name)
		pod = pods[0]
		second_pod_name = pod.metadata.name
		self.assertNotEqual(initial_pod_name, second_pod_name)
		self.assertNotEqual(pod.spec.node_name, initial_node)
		KubeUtils.wait_for_pod_to_be_running(second_pod_name)

if __name__ == '__main__':
	TestUtils.run_unittest()
