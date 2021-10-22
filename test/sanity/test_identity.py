import os
import time
import unittest

from google.protobuf.json_format import MessageToJson, MessageToDict

import driver.consts as Consts
from driver.config import Config
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.setup_and_teardown import start_server, start_containerized_server

from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning
from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.error_handlers import CatchRequestErrors

os.environ['DEVELOPMENT'] = 'True'

class TestIdentityService(TestCaseWithServerRunning):
	driver_server = None

	@classmethod
	def setUpClass(cls):
		config={}
		cls.driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')
		config['SOCKET_PATH'] = 'unix://%s' % cls.driver_server.csi_socket_path
		ConfigLoaderMock(config).load()
		cls.identityClient = IdentityClient()

	@classmethod
	def tearDownClass(cls):
		cls.driver_server.stop()

	@CatchRequestErrors
	def test_get_plugin_info(self):
		msg = self.identityClient.GetPluginInfo()
		self.assertEqual(msg.name, Config.DRIVER_NAME)
		self.assertEqual(msg.vendor_version, Config.DRIVER_VERSION)

	@CatchRequestErrors
	def test_get_plugin_capabilities(self):
		res = self.identityClient.GetPluginCapabilities()
		msg = MessageToDict(res)
		print(msg)

		expected = [
			'service.CONTROLLER_SERVICE',
			'service.VOLUME_ACCESSIBILITY_CONSTRAINTS',
			'volumeExpansion.ONLINE',
		]

		def capabilityToString(capability):
			if 'service' in capability:
				return 'service.' + capability['service']['type']
			elif 'volumeExpansion' in capability:
				return 'volumeExpansion.' + capability['volumeExpansion']['type']
			else:
				self.fail('Unknown Capability ' + capability)

		found = set()
		# make sure all reported capabilities are expected
		stringCapabilities = map(capabilityToString, msg['capabilities'])

		print('Got: %s' % stringCapabilities)

		for capability in stringCapabilities:
			self.assertIn(capability, expected, "Unexpected capability")
			found.add(capability)

		# make sure all expected capabilities were reported
		for capability in expected:
			self.assertIn(capability, found, "Missing capability %s" % capability)

	@CatchRequestErrors
	def test_probe(self):
		msg = self.identityClient.Probe()
		self.assertTrue(msg.ready)

if __name__ == '__main__':
	unittest.main()
