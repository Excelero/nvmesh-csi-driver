#!/usr/bin/env python2

import unittest

import test_utils
from test_utils import TestUtils, KubeUtils, NVMeshUtils, TestError

core_api = test_utils.core_api
storage_api = test_utils.storage_api

logger = TestUtils.get_logger()
namespace = TestUtils.get_test_namespace()

class StorageClassTest(object):
    def __init__(self, name, params):
        self.name = name
        self.params = params

def create_pvc_for_storage_class(pvc_name, sc_name):
    pvc = {
        'apiVersion': 'v1',
        'kind': 'PersistentVolumeClaim',
        'metadata': {
            'name': pvc_name,
            'namespace': namespace
        },
        'spec': {
            'accessModes': ['ReadWriteOnce'],
            'resources': {
                'requests': {
                    'storage': '3Gi'
                }
            },
            'storageClassName': sc_name
        }
    }

    return core_api.create_namespaced_persistent_volume_claim(namespace, pvc)

def verify_nvmesh_vol_properties(nvmesh_vol_name, params):
    volume = NVMeshUtils.get_nvmesh_volume_by_name(nvmesh_vol_name)

    for key, value in params.iteritems():
        if key == 'raidLevel':
            expected_val = NVMeshUtils.parse_raid_type(value)
            nvmesh_key = 'RAIDLevel'
        elif key in ['stripeWidth', 'stripeSize', 'numberOfMirrors']:
            expected_val = int(value)
            nvmesh_key = key
        else:
            expected_val = value
            nvmesh_key = key

        nvmesh_value = getattr(volume, nvmesh_key)
        TestUtils.assert_equal(expected_val, nvmesh_value, 'Wrong value in Volume {}'.format(nvmesh_key))

class TestStorageClassParameters(unittest.TestCase):
    test_cases = [
        StorageClassTest('concatenated', { 'raidLevel': 'concatenated' }),
        StorageClassTest('raid0-no-params', {'raidLevel': 'raid0'}),
        StorageClassTest('raid0-with-1-params', {'raidLevel': 'raid0', 'stripeSize': '64'}),
        StorageClassTest('raid0-with-2-params', {'raidLevel': 'raid0', 'stripeSize': '64', 'stripeWidth': '4'}),
        StorageClassTest('raid1', {'raidLevel': 'raid1'}),
        StorageClassTest('raid10-no-params', {'raidLevel': 'raid10'}),
        StorageClassTest('raid10-with-2-params', {'raidLevel': 'raid10', 'stripeSize': '32', 'stripeWidth': '2'}),
    ]

    def test_all_test_cases(self):
        raised = False

        try:
            for sc_test in TestStorageClassParameters.test_cases:
                pvc_name = 'pvc-{}'.format(sc_test.name)

                KubeUtils.create_storage_class(sc_test.name, sc_test.params)
                create_pvc_for_storage_class(pvc_name, sc_test.name)

                # wait for pvc to bound
                KubeUtils.wait_for_pvc_to_bound(pvc_name)

                # get the pv
                pv_name = KubeUtils.get_pv_name_from_pvc(pvc_name)

                # wait for nvmesh volume to be created
                nvmesh_vol_name = NVMeshUtils.csi_id_to_nvmesh_name(pv_name)
                NVMeshUtils.wait_for_nvmesh_volume(nvmesh_vol_name)

                # Verify NVMesh Volume  has the required properties
                verify_nvmesh_vol_properties(nvmesh_vol_name, sc_test.params)

                KubeUtils.delete_pvc(pvc_name)
                KubeUtils.delete_storage_class(sc_test.name)
        except Exception as ex:
            raised = True

        self.assertFalse(raised, 'Exception raised')

if __name__ == '__main__':
    #NVMeshUtils.delete_all_nvmesh_volumes()
    #KubeUtils.delete_all_non_default_storage_classes()
    TestUtils.run_unittest()