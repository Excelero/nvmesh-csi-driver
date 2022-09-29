import logging
import threading
import time
import unittest
from threading import Thread, Event

from NVMeshSDK.ConnectionManager import ManagementTimeout

from driver import topology
from driver import topology_utils
from driver.topology_utils import VolumeAPIPool
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock, DEFAULT_MOCK_CONFIG
from test.sanity.nvmesh_cluster_simulator.nvmesh_mgmt_sim import NVMeshManagementSim

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
		'C': {'management': {'servers': 'localhost:4010'}},
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
		cls.cluster1 = NVMeshManagementSim('cluster1', http_port=4000, ws_port=4001)
		cls.cluster1.start()
		cls.cluster1.wait_until_is_alive()

		cls.cluster2 = NVMeshManagementSim('cluster2', http_port=4010, ws_port=4011)
		cls.cluster2.start()
		cls.cluster2.wait_until_is_alive()

	@classmethod
	def tearDownClass(cls):
		cls.cluster1.stop()

	def tearDown(self):
		topology_utils.VolumeAPIPool._VolumeAPIPool__api_dict = {}
		topology_utils.VolumeAPIPool._VolumeAPIPool__zone_locks = {}

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

	def test_5_multiple_management_servers_per_zone(self):
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

	def test_4_api_creation_delayed_does_not_block_other_zones(self):
		original_volume_api = topology_utils.VolumeAPI

		def restore_original_api():
			topology_utils.VolumeAPI = original_volume_api

		self.addCleanup(restore_original_api)

		class MockConn(object):
			def __init__(self, servers, protocol):
				self.managementServers = [protocol + '://' + servers]

		class MockVolumeAPI(object):
			def __init__(self, user=None, password=None, logger=None, managementServers=None, managementProtocol='https', dbUUID=None):
				self.managementConnection = MockConn(managementServers, managementProtocol)
				if managementServers == 'localhost:4000':
					# Delay the request for zone A
					time.sleep(3)

		e = Event()
		apis = {}

		topology_utils.VolumeAPI = MockVolumeAPI

		def create_api_in_thread():
			e.set()
			print("A: %s" % topology_utils.VolumeAPI)
			a = VolumeAPIPool.get_volume_api_for_zone('A', logger)
			print("got A = %s" % a)
			apis['A'] = a

		t = Thread(target=create_api_in_thread)
		t.start()

		e.wait()
		print("getting C")
		time.sleep(1)
		print("C: %s" % topology_utils.VolumeAPI)
		b = VolumeAPIPool.get_volume_api_for_zone('C', logger)
		print("got C = %s" % b)

		# Make sure we returned before A
		self.assertNotIn('A', apis, "A VolumeAPI is already available, This probably means that the long creation of A blocked us from getting C")

		t.join()
		self.check_lock_released()

if __name__ == '__main__':
	unittest.main()
