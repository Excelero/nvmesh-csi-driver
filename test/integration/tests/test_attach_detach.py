#!/usr/bin/env python2

import unittest

from utils import TestUtils, KubeUtils, TestConfig

logger = TestUtils.get_logger()

class TestAttachDetach(unittest.TestCase):
	def test_step_1_create_volumes(self):
		storage_class = 'nvmesh-raid1'
		num_of_volumes = TestConfig.NumberOfVolumes
		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			pvc = KubeUtils.get_pvc_template(pvc_name, storage_class)
			KubeUtils.create_pvc(pvc)

		for i in range(num_of_volumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.wait_for_pvc_to_bound(pvc_name)

	def test_step_2_create_consumer_pods(self):
		for i in range(TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			pvc_name = 'vol-{}'.format(i)
			pod = KubeUtils.get_fs_consumer_pod_template(pod_name, pvc_name)

			KubeUtils.create_pod(pod)

		for i in range(TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.wait_for_pod_to_be_running(pod_name)

	def test_step_3_delete_pods(self):
		for i in range(TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.delete_pod(pod_name)

		for i in range(TestConfig.NumberOfVolumes):
			pod_name = 'consumer-{}'.format(i)
			KubeUtils.wait_for_pod_to_delete(pod_name)

	def test_step_4_delete_volumes(self):
		for i in range(TestConfig.NumberOfVolumes):
			pvc_name = 'vol-{}'.format(i)
			KubeUtils.delete_pvc(pvc_name)
			KubeUtils.wait_for_pvc_to_delete(pvc_name)

if __name__ == '__main__':
	TestUtils.run_unittest()