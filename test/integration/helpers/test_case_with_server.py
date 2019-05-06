import unittest

from grpc import StatusCode
from grpc._channel import _Rendezvous


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
	pass