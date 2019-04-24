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


if __name__ == '__main__':
	unittest.main()