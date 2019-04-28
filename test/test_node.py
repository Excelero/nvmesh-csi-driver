import unittest

from grpc import StatusCode
from grpc._channel import _Rendezvous

from test.clients.controller_client import ControllerClient
from test.helpers.test_case_with_server import TestCaseWithServerRunning

GB = 1024*1024*1024

def handleRequestError(action, grpcError):
	if grpcError._state.code == StatusCode.FAILED_PRECONDITION:
		print('{action} failed with code {code} details: {details}'.format(
			action=action,
			code=grpcError._state.code,
			details=grpcError._state.details))
	else:
		raise(grpcError)

class TestNodeService(TestCaseWithServerRunning):

	def test_empty_case(self):
		pass

	# def test_delete_volume(self):
	# 	ctrlClient = ControllerClient()
	# 	try:
	# 		msg = ctrlClient.DeleteVolume(volume_id="vol_1")
	# 		print(msg)
	# 	except _Rendezvous as ex:
	# 		handleRequestError('Create Volume', ex)

if __name__ == '__main__':
	unittest.main()