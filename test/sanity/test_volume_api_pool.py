import logging
import unittest

from NVMeshSDK.ConnectionManager import ManagementTimeout
from driver.topology import VolumeAPIPool
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class TestVolumeAPIPool(unittest.TestCase):
	ConfigLoaderMock().load()

	def check_lock_released(self):
		self.assertFalse(VolumeAPIPool.isLocked())

	def test_1_init(self):
		VolumeAPIPool.get_volume_api_for_zone('A')

	def test_2_get_volume_api(self):
		api = VolumeAPIPool.get_volume_api_for_zone('A')
		self.check_lock_released()

	def test_3_get_api_mgmt_not_responding(self):
		with self.assertRaises(ManagementTimeout):
			VolumeAPIPool.get_volume_api_for_zone('B')

		self.check_lock_released()

	def test_3_get_api_zone_missing(self):
		with self.assertRaises(ValueError):
			VolumeAPIPool.get_volume_api_for_zone('D')

		self.check_lock_released()


if __name__ == '__main__':
	unittest.main()
