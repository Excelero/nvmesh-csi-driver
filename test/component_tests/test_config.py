import unittest
from unittest import TestCase

from driver.config import ConfigIsReadOnly

class TestConfigFile(TestCase):
	def test_load(self):
		from driver.config import Config
		self.assertEquals(Config.management.protocol, 'https')

	def test_assignment(self):
		from driver.config import Config

		old_value = Config.management.protocol
		with self.assertRaises(ConfigIsReadOnly) as context:
			Config.management.protocol = 'http'

		self.assertTrue('Attempt to set attribute' in context.exception.message)
		self.assertEquals(old_value, Config.management.protocol)

	def test_read_key_not_exists(self):
		from driver.config import Config
		self.assertFalse(Config.somevalue.some_other)

if __name__ == '__main__':
	unittest.main()