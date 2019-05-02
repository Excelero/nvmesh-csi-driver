import socket
import unittest

from test.clients.node_client import NodeClient
from test.helpers.error_handlers import CatchRequestErrors
from test.helpers.test_case_with_server import TestCaseWithServerRunning

GB = 1024*1024*1024
VOL_ID = "vol_1"

class TestNodeService(TestCaseWithServerRunning):
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self._client = NodeClient()

	@CatchRequestErrors
	def test_get_info(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, socket.gethostname())

	@CatchRequestErrors
	def test_get_capabilities(self):
		res = self._client.NodeGetCapabilities()
		self.assertListEqual([], list(res.capabilities))

	# @CatchRequestErrors
	# def test_node_publish_volume(self):
	# 	res = self._client.NodePublishVolume(volume_id=VOL_ID)
	# 	print(res)
	#
	# @CatchRequestErrors
	# def test_node_unpublish_volume(self):
	# 	res = self._client.NodeUnpublishVolume(volume_id=VOL_ID)
	# 	print(res)

if __name__ == '__main__':
	unittest.main()