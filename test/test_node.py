import socket
import unittest

from grpc import StatusCode
from grpc._channel import _Rendezvous

from test.clients.node_client import NodeClient
from test.helpers.test_case_with_server import TestCaseWithServerRunning

GB = 1024*1024*1024
VOL_ID = "vol_1"

def handleGRPCError(action, grpcError):
	if grpcError._state.code == StatusCode.FAILED_PRECONDITION:
		print('{action} failed with code {code} details: {details}'.format(
			action=action,
			code=grpcError._state.code,
			details=grpcError._state.details))
	else:
		raise(grpcError)

class CatchRequestErrors(object):
	def __init__(self, action_name):
		self.action_name = action_name

	def __enter__(self):
		pass

	def __exit__(self, type, value, traceback):
		if type == _Rendezvous:
			handleGRPCError(self.action_name, value)

class TestNodeService(TestCaseWithServerRunning):
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self._client = NodeClient()

	def test_get_info(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, socket.gethostname())

	def test_get_capabilities(self):
		res = self._client.NodeGetCapabilities()
		self.assertListEqual([], list(res.capabilities))

	def test_node_publish_volume(self):
		res = self._client.NodePublishVolume(volume_id=VOL_ID)
		print(res)

	def test_node_unpublish_volume(self):
		res = self._client.NodeUnpublishVolume(volume_id=VOL_ID)
		print(res)

if __name__ == '__main__':
	unittest.main()