#!/usr/bin/env python2

import unittest


from utils import TestUtils, KubeUtils, NVMeshUtils

logger = TestUtils.get_logger()

class TestStorageClassParameters(unittest.TestCase):
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

	def test_raid1_with_enable_crc_check(self):
		self._test_storage_class_case('raid1', {'raidLevel': 'raid1', 'enableCrcCheck': 'true'})

	def test_raid10_no_params(self):
		self._test_storage_class_case('raid10-no-params', {'raidLevel': 'raid10'})

	def test_raid10_with_2_params(self):
		self._test_storage_class_case('raid10-with-2-params', {'raidLevel': 'raid10', 'stripeSize': '32', 'stripeWidth': '2'})

	def test_ec_no_separation_2_plus_1(self):
		ec_params = {
			'raidLevel': 'ec',
			'dataBlocks': '2',
			'parityBlocks': '1',
			'protectionLevel': 'Ignore Separation',
		}
		self._test_storage_class_case('ec-no-separation', ec_params)

	def test_ec_2_plus_1_no_sep_with_disable_crc(self):
		ec_params = {
			'raidLevel': 'ec',
			'dataBlocks': '2',
			'parityBlocks': '1',
			'protectionLevel': 'Ignore Separation',
			'enableCrcCheck': 'false'
		}
		self._test_storage_class_case('ec-disable-crc-check', ec_params)

	def _test_storage_class_case(self, sc_name, params):
		pvc_name = 'pvc-{}'.format(sc_name)

		KubeUtils.create_storage_class(sc_name, params)
		self.addCleanup(lambda: KubeUtils.delete_storage_class(sc_name))

		additional_fields = {
			'description': 'Storage Class Parameters test for ' + sc_name
		}

		KubeUtils.create_pvc_and_wait_to_bound(self, pvc_name, sc_name, **additional_fields)

		nvmesh_vol_name = KubeUtils.get_nvmesh_vol_name_from_pvc_name(pvc_name)
		mgmt_address = NVMeshUtils.wait_for_nvmesh_volume(nvmesh_vol_name)

		# Verify NVMesh Volume has the required properties
		NVMeshUtils.wait_for_nvmesh_vol_properties(nvmesh_vol_name, params, self)

if __name__ == '__main__':
	TestUtils.run_unittest()
