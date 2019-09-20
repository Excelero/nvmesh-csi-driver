import unittest

from driver.common import Consts
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning
from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.error_handlers import CatchRequestErrors


class TestIdentityService(TestCaseWithServerRunning):
	@CatchRequestErrors
	def test_get_plugin_info(self):
		identityClient = IdentityClient()
		msg = identityClient.GetPluginInfo()
		self.assertEqual(msg.name, Consts.DRIVER_NAME)
		self.assertEqual(msg.vendor_version, Consts.DRIVER_VERSION)

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