import os
import unittest
from threading import Thread

from grpc import StatusCode
import driver.consts as Consts
from driver import consts

from driver.csi.csi_pb2 import NodeServiceCapability, Topology
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.setup_and_teardown import start_server
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning

from test.sanity.clients.node_client import NodeClient
from test.sanity.helpers.error_handlers import CatchRequestErrors

GB = pow(1024, 3)
VOL_ID = "vol_1"
MOCK_NODE_ID = "node-1"
TOPOLOGY_SINGLE_ZONE = {'zones': {'zone_1': {'management': {'servers': 'localhost:4000'}}}}
TOPOLOGY_MULTIPLE_ZONES = Topology(segments={Consts.TopologyKey.ZONE: 'zone_1'})


os.environ['DEVELOPMENT'] = 'TRUE'

class TestNodeService(TestCaseWithServerRunning):
	driver_server = None

	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self.driver_server = None

	@staticmethod
	def restart_server_with_topology(topology):
		TestNodeService.driver_server.stop()

		config = {
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': topology
		}

		ConfigLoaderMock(config).load()

		TestNodeService.driver_server = start_server(Consts.DriverType.Node, MOCK_NODE_ID)

	@classmethod
	def setUpClass(cls):
		config = {
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': TOPOLOGY_SINGLE_ZONE
		}
		ConfigLoaderMock(config).load()
		os.environ['DEVELOPMENT'] = 'TRUE'
		#cls.driver_server = start_server(Consts.DriverType.Node, config, MOCK_NODE_ID)
		cls._client = NodeClient()

	@classmethod
	def tearDownClass(cls):
		print('stopping server')
		# cls.driver_server.stop()
		print('server stopped')

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
	def test_get_info_node_not_found_in_any_mgmt(self):
		topology = {
				'zones': {
					"A": {"management": {"servers": 'unreachable-server-1'}},
					"B": {"management": {"servers": 'unreachable-server-1'}},
					"C": {"management": {"servers": 'unreachable-server-1'}},
				}
			}

		TestNodeService.restart_server_with_topology(topology)

		def restore_default_server():
			TestNodeService.restart_server_with_topology(TOPOLOGY_SINGLE_ZONE)

		self.addCleanup(restore_default_server)

		def do_request():
			return self._client.NodeGetInfo()

		self.assertReturnsGrpcError(do_request, StatusCode.INTERNAL, "Could not find node")


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

		self.assertReturnsGrpcError(do_request, StatusCode.INVALID_ARGUMENT, "Device not formatted with FileSystem")

class TestNodeServiceGracefulShutdown(TestCaseWithServerRunning):
	def test_node_graceful_shutdown(self):
		config = {
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': TOPOLOGY_SINGLE_ZONE,
			'LOG_LEVEL': 'DEBUG',
		}
		ConfigLoaderMock(config).load()
		os.environ['DEVELOPMENT'] = 'TRUE'

		driver_server = start_server(Consts.DriverType.Node, MOCK_NODE_ID)
		client = NodeClient()

		results = []
		def run_get_info(results):
			print('Calling GetInfo')
			res = client.NodeGetInfo()
			results.append(res.node_id)

		thread = Thread(target=run_get_info, args=(results,))
		thread.start()

		print('Stopping the gRPC server')
		driver_server.stop()

		thread.join()

		self.assertEquals(len(results), 1)




if __name__ == '__main__':
	unittest.main()
