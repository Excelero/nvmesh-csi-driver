#!/usr/bin/env python2
import argparse
import unittest

from test.integration.tests.test_access_modes import TestAccessModes
from test.integration.tests.test_attach_detach import TestAttachDetach
from test.integration.tests.test_block_volume import TestBlockVolume
from test.integration.tests.test_default_storage_classes import TestAllRAIDTypes
from test.integration.tests.test_file_system_volume import TestFileSystemVolume
from test.integration.tests.test_migration import TestMigration
from test.integration.tests.test_storage_class_params import TestStorageClassParameters
from test.integration.tests.utils import CollectCsiLogsTestResult, TestUtils, TestConfig

def get_parser():
	parser = argparse.ArgumentParser(description='NVMesh CSI Driver - Integration Testing')
	parser.add_argument('--num-of-volumes', type=int, default=1, help='Number of Volumes for scale testing, default is 1')
	parser.add_argument('--skip-ec-volumes', action='store_true', help='Skip testing of EC Volumes')
	return parser

if __name__ == '__main__':
	parser = get_parser()
	args = parser.parse_args()

	TestConfig.SkipECVolumes = args.skip_ec_volumes
	TestConfig.NumberOfVolumes = args.num_of_volumes

	TestUtils.clear_environment()

	test_classes_to_run = [
		TestAllRAIDTypes,
		TestStorageClassParameters,
		TestAttachDetach,
		TestFileSystemVolume,
		TestBlockVolume,
		TestMigration,
		TestAccessModes
	]

	loader = unittest.TestLoader()

	suites_list = []
	for test_class in test_classes_to_run:
		suite = loader.loadTestsFromTestCase(test_class)
		suites_list.append(suite)

	all_tests_suite = unittest.TestSuite(suites_list)

	runner = unittest.TextTestRunner(resultclass=CollectCsiLogsTestResult)
	results = runner.run(all_tests_suite)