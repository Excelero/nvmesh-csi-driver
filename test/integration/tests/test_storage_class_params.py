#!/usr/bin/env python2

import unittest

import test_utils
from test_utils import TestUtils, KubeUtils, NVMeshUtils

core_api = test_utils.core_api
storage_api = test_utils.storage_api

logger = TestUtils.get_logger()
namespace = TestUtils.get_test_namespace()


class TestStorageClassParameters(unittest.TestCase):
    def _create_pvc_for_storage_class(self, pvc_name, sc_name):
        pvc = KubeUtils.get_pvc_template(pvc_name, storage_class_name=sc_name)
        return core_api.create_namespaced_persistent_volume_claim(namespace, pvc)

    def test_concatenated(self):
        self._test_storage_class_case('concatenated', { 'raidLevel': 'concatenated' })

    def test_raid0_no_params(self):
        self._test_storage_class_case('raid0-no-params', {'raidLevel': 'raid0'})

    def test_raid0_with_1_param(self):
        self._test_storage_class_case('raid0-with-1-params', {'raidLevel': 'raid0', 'stripeSize': '64'})

    def test_raid0_with_2_params(self):
        self._test_storage_class_case('raid0-with-2-params', {'raidLevel': 'raid0', 'stripeSize': '64', 'stripeWidth': '4'})

    def test_raid1(self):
        self._test_storage_class_case('raid1', {'raidLevel': 'raid1'})

    def test_raid10_no_params(self):
        self._test_storage_class_case('raid10-no-params', {'raidLevel': 'raid10'})

    def test_raid10_with_2_params(self):
        self._test_storage_class_case('raid10-with-2-params', {'raidLevel': 'raid10', 'stripeSize': '32', 'stripeWidth': '2'})

    def _test_storage_class_case(self, sc_name, params):
        pvc_name = 'pvc-{}'.format(sc_name)

        KubeUtils.create_storage_class(sc_name, params)
        self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))

        self._create_pvc_for_storage_class(pvc_name, sc_name)
        self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_name))

        # wait for pvc to bound
        KubeUtils.wait_for_pvc_to_bound(pvc_name)

        nvmesh_vol_name = KubeUtils.get_nvmesh_vol_name_from_pvc_name(pvc_name)
        NVMeshUtils.wait_for_nvmesh_volume(nvmesh_vol_name)

        # Verify NVMesh Volume has the required properties
        NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, params, self)

if __name__ == '__main__':
    TestUtils.run_unittest()