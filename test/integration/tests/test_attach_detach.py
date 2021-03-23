#!/usr/bin/env python2

import unittest

from utils import TestUtils, KubeUtils, TestConfig

logger = TestUtils.get_logger()

class TestAttachDetach(unittest.TestCase):
	def _create_volumes(self, num_of_volumes):
		storage_class = 'nvmesh-raid1'
		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			pvc = KubeUtils.get_pvc_template(pvc_name, storage_class)
			KubeUtils.create_pvc(pvc)

	def _wait_for_volumes(self, num_of_volumes):
		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.wait_for_pvc_to_bound(pvc_name, attempts=60)

	def _create_consumer_pods(self, num_of_volumes):
		for i in range(num_of_volumes):
			pod_name = 'consumer-{}'.format(i)
			pvc_name = 'vol-{}'.format(i)
			pod = KubeUtils.get_fs_consumer_pod_template(pod_name, pvc_name)

			KubeUtils.create_pod(pod)

	def _wait_for_pods(self, num_of_volumes):
		for i in range(num_of_volumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.wait_for_pod_to_be_running(pod_name)

	@staticmethod
	def _delete_pods(num_of_volumes):
		for i in range(num_of_volumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.delete_pod(pod_name)

		for i in range(num_of_volumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.wait_for_pod_to_delete(pod_name)

	@staticmethod
	def _delete_volumes(num_of_volumes):
		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.delete_pvc(pvc_name)
			KubeUtils.wait_for_pvc_to_delete(pvc_name)

	def test_attach_detach(self):
		num_of_instances = TestConfig.NumberOfVolumes

		self._create_volumes(num_of_instances)
		self.addCleanup(lambda:self._delete_volumes(num_of_instances))

		self._wait_for_volumes(num_of_instances)

		self._create_consumer_pods(num_of_instances)
		self.addCleanup(lambda: self._delete_pods(num_of_instances))

		self._wait_for_pods(num_of_instances)


if __name__ == '__main__':
	TestUtils.run_unittest()