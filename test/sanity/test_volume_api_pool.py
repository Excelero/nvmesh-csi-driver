import logging
import unittest

from NVMeshSDK.ConnectionManager import ManagementTimeout
from driver.topology_utils import VolumeAPIPool
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.nvmesh_cluster_simulator.simulate_cluster import NVMeshCluster

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class TestVolumeAPIPool(unittest.TestCase):
	ConfigLoaderMock().load()
	cluster1 = None

	@classmethod
	def setUpClass(cls):
		cls.cluster1 = NVMeshCluster('cluster1')
		cls.cluster1.start()

	@classmethod
	def tearDownClass(cls):
		cls.cluster1.stop()


	def check_lock_released(self):
		self.assertFalse(VolumeAPIPool.isLocked())

	def test_1_init(self):
		VolumeAPIPool.get_volume_api_for_zone('A', logger)

	def test_2_get_volume_api(self):
		api = VolumeAPIPool.get_volume_api_for_zone('A', logger)
		self.check_lock_released()

	def test_3_get_api_mgmt_not_responding(self):
		with self.assertRaises(ManagementTimeout):
			VolumeAPIPool.get_volume_api_for_zone('B', logger)

		self.check_lock_released()

	def test_3_get_api_zone_missing(self):
		with self.assertRaises(ValueError):
			VolumeAPIPool.get_volume_api_for_zone('D', logger)

		self.check_lock_released()


if __name__ == '__main__':
	unittest.main()
