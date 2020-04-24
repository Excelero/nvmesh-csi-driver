#!/usr/bin/env python2

import unittest

from test.integration.tests.test_attach_detach import TestAttachDetachExtend
from test.integration.tests.test_default_storage_classes import TestAllRAIDTypes
from test.integration.tests.test_storage_class_params import TestStorageClassParameters
from test.integration.tests.test_utils import CollectCsiLogsTestResult, TestUtils

if __name__ == '__main__':
    TestUtils.clear_environment()

    test_classes_to_run = [
        TestAllRAIDTypes,
        TestStorageClassParameters,
        TestAttachDetachExtend
    ]

    loader = unittest.TestLoader()

    suites_list = []
    for test_class in test_classes_to_run:
        suite = loader.loadTestsFromTestCase(test_class)
        suites_list.append(suite)

    all_tests_suite = unittest.TestSuite(suites_list)

    runner = unittest.TextTestRunner(resultclass=CollectCsiLogsTestResult)
    results = runner.run(all_tests_suite)