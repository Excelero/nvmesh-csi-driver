import unittest

from driver.common import Consts
from test.clients.identity_client import IdentityClient
from test.helpers.test_case_with_server import TestCaseWithServerRunning


class TestIdentityService(TestCaseWithServerRunning):

	def test_get_plugin_info(self):
		identityClient = IdentityClient()
		msg = identityClient.GetPluginInfo()
		self.assertEqual(msg.name, Consts.IDENTITY_NAME)
		self.assertEqual(msg.vendor_version, Consts.SERVICE_VERSION)

	def test_get_plugin_capabilities(self):
		identityClient = IdentityClient()
		msg = identityClient.GetPluginCapabilities()
		print(msg)

	def test_probe(self):
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		self.assertTrue(msg.ready)

if __name__ == '__main__':
	unittest.main()