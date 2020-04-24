#!/usr/bin/env python2

import unittest

import test_utils
from test_utils import TestUtils, KubeUtils, NVMeshUtils

core_api = test_utils.core_api
storage_api = test_utils.storage_api

logger = TestUtils.get_logger()
namespace = TestUtils.get_test_namespace()

class TestAllRAIDTypes(unittest.TestCase):

    def _test_raid_type(self, raid_type):
        storage_class_name = 'nvmesh-{}'.format(raid_type)
        pvc_name = storage_class_name
        pvc_yaml = KubeUtils.get_pvc_template(pvc_name, storage_class_name)

        # create the PVC
        KubeUtils.create_pvc(pvc_yaml)

        # wait for pvc to bound
        KubeUtils.wait_for_pvc_to_bound(pvc_name)

        # wait for nvmesh volume to be created
        nvmesh_vol_name = KubeUtils.get_nvmesh_vol_name_from_pvc_name(pvc_name)
        NVMeshUtils.wait_for_nvmesh_volume(nvmesh_vol_name)

        # verify NVMesh Volumes Properties
        NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, { 'raidLevel': raid_type }, self)

        def cleanup_volume():
            KubeUtils.delete_pvc(pvc_name)
            KubeUtils.wait_for_pvc_to_delete(pvc_name)

        self.addCleanup(cleanup_volume)

    def test_concatenated(self):
        self._test_raid_type('concatenated')

    def test_raid0(self):
        self._test_raid_type('raid0')

    def test_raid1(self):
        self._test_raid_type('raid1')

    def test_raid10(self):
        self._test_raid_type('raid10')

    @unittest.skipIf(test_utils.TestConfig.SkipECVolumes, "Skipping EC Volumes")
    def test_ec_single_target_redundancy(self):
        self._test_raid_type('ec_single_target_redundancy')

    @unittest.skipIf(test_utils.TestConfig.SkipECVolumes, "Skipping EC Volumes")
    def test_ec_dual_target_redundancy(self):
        self._test_raid_type('ec_dual_target_redundancy')

if __name__ == '__main__':
    TestUtils.run_unittest()
