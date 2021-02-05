import json
import socket
import unittest

from google.protobuf.json_format import MessageToJson
from grpc import StatusCode
import driver.consts as Consts
from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI
from NVMeshSDK.Entities.TargetClass import TargetClass
from driver.common import NVMeshSDKHelper

from driver.csi.csi_pb2 import NodeServiceCapability, VolumeCapability
from test.sanity.helpers.setup_and_teardown import start_server
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning

from test.sanity.clients.node_client import NodeClient
from test.sanity.helpers.error_handlers import CatchRequestErrors

GB = pow(1024, 3)
VOL_ID = "vol_1"
MOCK_NODE_ID = "nvme115.excelero.com"

class TestNodeService(TestCaseWithServerRunning):
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self.driver_server = None

	def setUp(self):
		self.driver_server = start_server(Consts.DriverType.Node, MOCK_NODE_ID)
		self._client = NodeClient()

	def tearDown(self):
		self.driver_server.stop()

	@CatchRequestErrors
	def test_get_info_basic_test(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, MOCK_NODE_ID)


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

		self.assertReturnsGrpcError(do_request, StatusCode.INTERNAL, "Timed-out after waiting")

	@CatchRequestErrors
	def test_node_unstage_volume(self):
		self._client.NodeUnstageVolume(volume_id=VOL_ID)

	@CatchRequestErrors
	def test_node_publish_volume(self):
		def do_request():
			return self._client.NodePublishVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "was not found")

	@CatchRequestErrors
	def test_node_unpublish_volume(self):
		def do_request():
			return self._client.NodeUnpublishVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "mount path")

	@CatchRequestErrors
	def test_node_expand_volume(self):
		def do_request():
			return self._client.NodeExpandVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.INVALID_ARGUMENT, "unknown fs_type")

if __name__ == '__main__':
	unittest.main()
