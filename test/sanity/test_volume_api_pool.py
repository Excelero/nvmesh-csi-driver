import logging
import unittest

from NVMeshSDK.ConnectionManager import ManagementTimeout
from driver.topology_utils import VolumeAPIPool
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock, DEFAULT_MOCK_CONFIG
from test.sanity.nvmesh_cluster_simulator.simulate_cluster import NVMeshCluster

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

TOPOLOGY = {
	'zones': {
		'A': {'management': {'servers': 'localhost:4000'}},
		'B': {'management': {'servers': 'wrong-address:4000'}},
	}
}

DEFAULT_CONFIG = DEFAULT_MOCK_CONFIG.copy()
DEFAULT_CONFIG['TOPOLOGY'] = TOPOLOGY

class TestVolumeAPIPool(unittest.TestCase):
	ConfigLoaderMock(DEFAULT_CONFIG).load()
	cluster1 = None

	@classmethod
	def setUpClass(cls):
		super(TestVolumeAPIPool, cls).setUpClass()
		cls.cluster1 = NVMeshCluster('cluster1')
		cls.cluster1.start()
		cls.cluster1.wait_until_is_alive()

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

	def test_4_multiple_management_servers_per_zone(self):
		cluster1mgmt2 = NVMeshCluster('cluster1mgmt2', http_port=4010, ws_port=4011)
		cluster1mgmt2.start()
		cluster1mgmt2.wait_until_is_alive()
		self.addCleanup(lambda: cluster1mgmt2.stop())

		multi_mgmt_servers_topology = {
			'zones': {
				'A': {'management': {'servers': 'unavailable:4000,localhost:4000,localhost:4010'}},
			}
		}

		config = DEFAULT_MOCK_CONFIG.copy()
		config['TOPOLOGY'] = multi_mgmt_servers_topology
		ConfigLoaderMock(config).load()

		try:
			zone_a_api = VolumeAPIPool.get_volume_api_for_zone('A', logger)
		except ValueError as ex:
			self.fail('Got ValueError exception: %s' % ex)

if __name__ == '__main__':
	unittest.main()
