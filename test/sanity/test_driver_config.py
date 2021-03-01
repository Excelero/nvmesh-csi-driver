import unittest
from unittest import TestCase
import os

from driver.config import ConfigError, config_loader, Config

@unittest.skip
class TestConfigFile(TestCase):
	def test_load(self):
		from driver.config import Config
		self.assertEquals(Config.MANAGEMENT_PROTOCOL, 'https')

	def test_fails_on_missing_management_servers(self):
		del os.environ['MANAGEMENT_SERVERS']

		def tryImport():
			config_loader.load()
			print(Config.MANAGEMENT_SERVERS)

		self.assertRaises(ConfigError, tryImport)

	def test_fails_on_empty_management_servers(self):
		os.environ['MANAGEMENT_SERVERS'] = ''
		def tryImport():
			config_loader.load()
			print(Config.MANAGEMENT_SERVERS)

		self.assertRaises(ConfigError, tryImport)

if __name__ == '__main__':
	unittest.main()