import unittest

from driver.common import Consts
from test.integration.helpers.test_case_with_server import TestCaseWithServerRunning
from test.integration.clients.identity_client import IdentityClient
from test.integration.helpers.error_handlers import CatchRequestErrors


class TestIdentityService(TestCaseWithServerRunning):
	@CatchRequestErrors
	def test_get_plugin_info(self):
		identityClient = IdentityClient()
		msg = identityClient.GetPluginInfo()
		self.assertEqual(msg.name, Consts.PLUGIN_NAME)
		self.assertEqual(msg.vendor_version, Consts.PLUGIN_VERSION)

	@CatchRequestErrors
	def test_get_plugin_capabilities(self):
		identityClient = IdentityClient()
		msg = identityClient.GetPluginCapabilities()
		print(msg)

	@CatchRequestErrors
	def test_probe(self):
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		self.assertTrue(msg.ready)

if __name__ == '__main__':
	unittest.main()