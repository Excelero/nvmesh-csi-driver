import json
import os
import time
import unittest
from threading import Thread

from grpc import StatusCode
import driver.consts as Consts
from driver import consts

from driver.csi.csi_pb2 import NodeServiceCapability, Topology
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.setup_and_teardown import start_server, start_containerized_server
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning

from test.sanity.clients.node_client import NodeClient, STAGING_PATH_TEMPLATE
from test.sanity.helpers.error_handlers import CatchRequestErrors, CatchNodeDriverErrors

GB = pow(1024, 3)
VOL_ID = "vol_1"
NODE_ID_1 = "node-1"
TOPOLOGY_SINGLE_ZONE = {'zones': {'zone_1': {'management': {'servers': 'localhost:4000'}}}}
TOPOLOGY_MULTIPLE_ZONES = Topology(segments={Consts.TopologyKey.ZONE: 'zone_1'})


os.environ['DEVELOPMENT'] = 'TRUE'

class TestNodeService(TestCaseWithServerRunning):
	driver_server = None

	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self.driver_server = None

	@staticmethod
	def restart_server(new_config=None):
		TestNodeService.driver_server.stop()

		config = new_config or TestNodeService.driver_server.config
		ConfigLoaderMock(config).load()
		TestNodeService.driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')

	@classmethod
	def setUpClass(cls):
		topology = {
				'type': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
				'zones': TOPOLOGY_SINGLE_ZONE['zones']
			}
		config = {'topology': json.dumps(topology)}
		cls.driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')
		config['SOCKET_PATH'] = 'unix://%s' % cls.driver_server.csi_socket_path
		ConfigLoaderMock(config).load()
		cls._client = NodeClient()

		# To keep the container running after a test un-comment the following line:
		#TestNodeService.driver_server.keep_container_on_finish()

	@classmethod
	def tearDownClass(cls):
		print('stopping server')
		cls.driver_server.stop()
		print('server stopped')

	@CatchRequestErrors
	def test_get_info_basic_test(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, NODE_ID_1)

	@CatchNodeDriverErrors(NODE_ID_1)
	def test_get_info_with_topology(self):
		self.restart_server(TestNodeService.driver_server.config)

		zones_dict = {
			'A': {'nodes': ['node-2', NODE_ID_1, 'node-3']},
			'B': {'nodes': ['node-4', 'node-5']}
		}

		TestNodeService.driver_server.set_topology_config_map(json.dumps(zones_dict))

		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, NODE_ID_1)

		topology_info = res.accessible_topology.segments
		print(topology_info)
		# This is configured in ConfigLoaderMock.TOPOLOGY
		self.assertEquals(topology_info.get(Consts.TopologyKey.ZONE), 'A')

	@CatchRequestErrors
	def test_get_info_node_not_found_in_any_mgmt(self):
		self.restart_server()
		TestNodeService.driver_server.set_topology_config_map(json.dumps({}))

		result_bucket = {}
		def do_request(result_bucket):
			res = self._client.NodeGetInfo()
			result_bucket['res'] = res

		time.sleep(2)

		t = Thread(target=do_request, args=(result_bucket,))
		t.start()

		# Make sure the response does not return
		attempts = 5
		while attempts:
			t.join(timeout=1)
			self.assertTrue(t.isAlive())
			attempts = attempts - 1

		zones_dict = {'zoneA': {'nodes': [NODE_ID_1]}}
		TestNodeService.driver_server.set_topology_config_map(json.dumps(zones_dict))
		t.join(timeout=8)
		result = result_bucket.get('res')
		self.assertTrue(result)
		self.assertEquals(result.node_id, NODE_ID_1)

	@CatchRequestErrors
	def test_get_capabilities(self):
		res = self._client.NodeGetCapabilities()
		expected = [NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME, NodeServiceCapability.RPC.EXPAND_VOLUME]
		self.assertListEqual(expected, [item.rpc.type for item in list(res.capabilities)])

	@CatchRequestErrors
	def test_node_stage_volume(self):
		TestNodeService.driver_server.set_nvmesh_attach_volumes_content("""
import sys
import json
import os

MB = 1024 * 1024
GB = MB * 1024
vol_id = sys.argv[-1]

device_path = "/dev/nvmesh/%s" % vol_id 
with open(device_path, "wb") as f:
	f.truncate(MB * 100)

proc_dir = '/simulated/proc/nvmeibc/volumes/%s'  % vol_id
proc_status_file = "%s/status.json" % proc_dir

try:
	os.makedirs(proc_dir)
except:
	pass
with open(proc_status_file, "w") as f:
	f.write(json.dumps({'dbg':'0x200'}))
print('{ "status": "success", "volumes": { "%s": { "status": "Attached IO Enabled" } } }' % vol_id)
		""")
		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		r = self._client.NodeStageVolume(volume_id=VOL_ID)
		print(r)
		print("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_node_publish_volume(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_path = '/var/lib/kubelet/pods/fake-pod/volumes/kubernetes.io~csi/vol_1/'
		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_path)
		r = self._client.NodePublishVolume(volume_id=VOL_ID)
		print(r)

	@CatchRequestErrors
	def test_node_unpublish_volume(self):
		r = self._client.NodeUnpublishVolume(volume_id=VOL_ID)
		print(r)

	@CatchRequestErrors
	def test_node_expand_volume(self):
		def do_request():
			return self._client.NodeExpandVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.INVALID_ARGUMENT, "Device not formatted with FileSystem")

class TestNodeServiceGracefulShutdown(TestCaseWithServerRunning):
	def test_node_graceful_shutdown(self):
		topology = {
			'type': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'zones': TOPOLOGY_SINGLE_ZONE['zones']
		}
		config = {'topology': json.dumps(topology)}
		driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')
		config['SOCKET_PATH'] = 'unix://%s' % driver_server.csi_socket_path
		ConfigLoaderMock(config).load()
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
