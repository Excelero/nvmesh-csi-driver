import json
import logging
import os
import time

from driver.zone_topology_fetcher import ZoneTopologyFetcherThread
from test.sanity.nvmesh_cluster_simulator.simulate_cluster import create_clusters

os.environ['DEVELOPMENT'] = 'TRUE'

from driver import consts, config_map_api
from driver.common import LoggerUtils
from driver.config_map_api import watch
from driver.mgmt_websocket_client import LoginFailed, FailedToConnect
from driver.topology import Topology
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning


class TestTopologyFetcherThread(TestCaseWithServerRunning):
	'''
	These are test cases to check that while the server terminates all running requests are able to finish successfully
	'''
	clusters = None

	@classmethod
	def setUpClass(cls):
		cls.clusters = create_clusters(num_of_clusters=2, num_of_client_per_cluster=3)

		for cluster in cls.clusters:
			cluster.start()

		for cluster in cls.clusters:
			cluster.wait_until_is_alive()

	@classmethod
	def tearDownClass(cls):
		for cluster in cls.clusters:
			cluster.stop()

	def test_all_zones_are_accessible(self):
		clusters = TestTopologyFetcherThread.clusters
		LoggerUtils.add_stdout_handler(logging.getLogger('topology-service'))

		os.environ['DEVELOPMENT'] = 'TRUE'
		topology = {
				"zones": {
						"A": {
							"management": {
								"servers": clusters[0].get_mgmt_server_string(),
								"ws_port": clusters[0].ws_port
							}
						},
						"B": {
							"management": {
								"servers": clusters[1].get_mgmt_server_string(),
								"ws_port": clusters[1].ws_port
							}
						}
				}
			}

		config = {
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': topology,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'DEBUG'
		}

		ConfigLoaderMock(config).load()

		from driver.topology_service import TopologyService

		topology_service = TopologyService()
		topology_service.run()
		self.addCleanup(lambda: topology_service.stop())

		time.sleep(15)
		nodes_topology = topology_service.topology.nodes

		expected_topology = {}

		for client in clusters[0].clients:
			expected_topology[client] = 'A'

		for client in clusters[1].clients:
			expected_topology[client] = 'B'

		self.assertEqual(json.dumps(expected_topology, sort_keys=True), json.dumps(nodes_topology, sort_keys=True))

	def test_listen_on_client_changes_fail_to_login(self):
		clusters = TestTopologyFetcherThread.clusters

		zone_name = 'zone_1'
		zone_config = {
			'management': {
				'servers': clusters[0].get_mgmt_server_string(),
				'ws_port': clusters[0].ws_port,
				'username': 'someone'
			}
		}

		topology = Topology()
		with topology.lock:
			topology.set_zone_config_without_lock(zone_name, zone_config)
		fetcher = ZoneTopologyFetcherThread(zone_name, zone_config, topology, None)

		with self.assertRaises(LoginFailed):
			fetcher.listen_on_node_changes_on_zone(zone_name, zone_config)

	def test_listen_on_client_changes_fail_to_connect(self):
		clusters = TestTopologyFetcherThread.clusters

		zone_name = 'zone_1'
		zone_config = {
			'management': {
				'servers': clusters[0].get_mgmt_server_string(),
				'ws_port': 6123
			}
		}

		topology = Topology()
		topology.set_zone_config_without_lock(zone_name, zone_config)
		fetcher = ZoneTopologyFetcherThread(zone_name, zone_config, topology, None)

		with self.assertRaises(FailedToConnect):
			fetcher.listen_on_node_changes_on_zone(zone_name, zone_config)


	def test_listen_on_client_changes_fail_to_resolve_hostname(self):
		zone_name = 'zone_1'
		zone_config = {
			'management': {
				'servers': 'unknown-server',
			}
		}

		topology = Topology()
		topology.set_zone_config_without_lock(zone_name, zone_config)
		fetcher = ZoneTopologyFetcherThread(zone_name, zone_config, topology, None)

		with self.assertRaises(FailedToConnect):
			fetcher.listen_on_node_changes_on_zone(zone_name, zone_config)

	def test_watch_config_map_changes(self):
		CSI_CONFIG_MAP_NAME = 'nvmesh-csi-config'
		config_map_api.init()

		def print_event(event):
			event_type = event['type']
			obj_name = event['raw_object']['metadata'].get('name')
			print('%s %s' % (event_type, obj_name))

		watch(CSI_CONFIG_MAP_NAME, do_on_event=print_event)