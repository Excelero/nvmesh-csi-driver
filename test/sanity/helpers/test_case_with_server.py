import unittest

from grpc._channel import _Rendezvous

from test.sanity.helpers import config_map_api_mock
from test.sanity.helpers.sanity_log import setup_logging_level

class TestCaseWithGrpcErrorHandling(unittest.TestCase):
	def assertReturnsGrpcError(self, func, status_code, message_part=None):
		try:
			response = func()
			self.assertIsNone(response, 'Expected GRPC error but received: {}'.format(response))
		except _Rendezvous as ex:
			code = ex._state.code
			details = ex._state.details
			self.assertEquals(code, status_code, 'expected GRPC StatusCode {} but received {} with message "{}"'.format(status_code, code, details))
			if message_part:
				self.assertTrue(message_part in details, 'expected to find "{}" in error details but recevied: {}'.format(message_part, details))

class TestCaseWithServerRunning(TestCaseWithGrpcErrorHandling):
	@classmethod
	def setUpClass(cls):
		super(TestCaseWithServerRunning, cls).setUpClass()
		setup_logging_level()

		# This will mock the k8s core api object
		config_map_api_mock.init_mocked_api()
