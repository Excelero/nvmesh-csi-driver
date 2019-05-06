import socket
import unittest

import os
os.environ['MANAGEMENT_SERVERS'] = 'n115:4000'

from grpc import StatusCode

from driver.common import Consts
from driver.csi.csi_pb2 import NodeServiceCapability, VolumeCapability
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
		expected = [NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME, NodeServiceCapability.RPC.EXPAND_VOLUME]
		self.assertListEqual(expected, [ item.rpc.type for item in list(res.capabilities) ])

	@CatchRequestErrors
	def test_node_stage_volume_fail_with_no_block_device(self):
		def do_request():
			return self._client.NodeStageVolume(volume_id=VOL_ID,
												access_type=Consts.VolumeAccessType.BLOCK,
												access_mode=VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER)

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