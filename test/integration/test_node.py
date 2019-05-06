import socket
import unittest

from grpc import StatusCode

from driver.csi.csi_pb2 import NodeServiceCapability
from test.integration.helpers.test_case_with_server import TestCaseWithServerRunning
from test.integration.clients.node_client import NodeClient
from test.integration.helpers.error_handlers import CatchRequestErrors

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
		expected = [NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME]
		self.assertListEqual(expected, [ item.rpc.type for item in list(res.capabilities) ])

	@CatchRequestErrors
	def test_node_stage_volume(self):
		def do_request():
			return self._client.NodeStageVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "nvmesh volume {} was not found".format(VOL_ID))

	@CatchRequestErrors
	def test_node_unstage_volume(self):
		def do_request():
			return self._client.NodeUnstageVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "mount path")

	@CatchRequestErrors
	def test_node_publish_volume(self):
		def do_request():
			return self._client.NodePublishVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "nvmesh volume {} was not found".format(VOL_ID))

	@CatchRequestErrors
	def test_node_unpublish_volume(self):
		def do_request():
			return self._client.NodeUnpublishVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "mount path")


if __name__ == '__main__':
	unittest.main()