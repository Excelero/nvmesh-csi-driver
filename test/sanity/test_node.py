import socket
import unittest

from grpc import StatusCode
import driver.consts as Consts
from driver import consts

from driver.csi.csi_pb2 import NodeServiceCapability
from test.sanity.helpers.config_loader_mock import DEFAULT_CONFIG_TOPOLOGY, ConfigLoaderMock
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
		config = {
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': DEFAULT_CONFIG_TOPOLOGY
		}
		ConfigLoaderMock(config).load()

		self.driver_server = start_server(Consts.DriverType.Node, MOCK_NODE_ID)
		self._client = NodeClient()

	def tearDown(self):
		self.driver_server.stop()

	@CatchRequestErrors
	def test_get_info_basic_test(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, MOCK_NODE_ID)

	@CatchRequestErrors
	def test_get_info_with_topology(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, MOCK_NODE_ID)

		topology_info = res.accessible_topology.segments
		print(topology_info)
		# This is configured in ConfigLoaderMock.TOPOLOGY
		self.assertEquals(topology_info.get(Consts.TopologyKey.ZONE), 'A')

	@CatchRequestErrors
	def test_get_capabilities(self):
		res = self._client.NodeGetCapabilities()
		expected = [NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME, NodeServiceCapability.RPC.EXPAND_VOLUME]
		self.assertListEqual(expected, [ item.rpc.type for item in list(res.capabilities) ])

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
