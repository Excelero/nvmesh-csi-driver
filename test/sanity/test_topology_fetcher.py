import json
import logging
import os
import time
import unittest

from driver import consts
from driver.common import LoggerUtils
from driver.mgmt_websocket_client import LoginFailed, FailedToConnect
from driver.topology_fetcher import TopologyFetcher, Topology
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.sanity_test_config import SanityTestConfig
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning

mgmt_address_node_exists_wrong_port = '{}:{}'.format(SanityTestConfig.ManagementServers[0].split(':')[0], '4066')

TOPOLOGY = {
			"zones": {
					"A": {
						"management": {
							"servers": SanityTestConfig.ManagementServers[0]
						}
					},
					"B": {
						"management": {
							"servers": 'test-failure-fall-back.com:5000,%s' % SanityTestConfig.ManagementServers[1]
						}
					},
					"C": {
						"management": {
							"servers": mgmt_address_node_exists_wrong_port,
							"ws_port": 4067
						}
					},
					"long.zone.name.with.dots.and.numbers.123": {
						"management": {
							"servers": 'unknown-server'
						}
					},
				}
			}

class TestTopologyFetcher(TestCaseWithServerRunning):
	'''
	These are test cases to check that while the server terminates all running requests are able to finish successfully
	'''

	def test_topology_fetcher(self):
		LoggerUtils.add_stdout_handler(logging.getLogger('topology-service'))

		os.environ['DEVELOPMENT'] = 'TRUE'

		config = {
			'MANAGEMENT_SERVERS': None,
			'MANAGEMENT_PROTOCOL': None,
			'MANAGEMENT_USERNAME': None,
			'MANAGEMENT_PASSWORD': None,
			'TOPOLOGY_TYPE': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': TOPOLOGY
		}

		ConfigLoaderMock(config).load()

		from driver.topology_service import TopologyService

		topology_service = TopologyService()
		topology_service.run()
		time.sleep(15)
		nodes_topology = topology_service.topology.nodes

		expected_topology = {
			SanityTestConfig.Nodes[0]: 'A',
			SanityTestConfig.Nodes[1]: 'B'
		}
		self.assertEqual(json.dumps(nodes_topology, sort_keys=True), json.dumps(expected_topology, sort_keys=True))
		topology_service.stop()

	def test_listen_on_client_changes_fail_to_login(self):
		zone_name = 'zone_1'
		zone_config = {
			'management': {
				'servers': SanityTestConfig.ManagementServers[0],
				'username': 'someone'
			}
		}

		topology = Topology()
		topology.add_zone_config(zone_name, zone_config)
		fetcher = TopologyFetcher(topology=topology)

		with self.assertRaises(LoginFailed):
			fetcher.listen_on_node_changes_on_zone(zone_name, zone_config)

	def test_listen_on_client_changes_fail_to_connect(self):
		zone_name = 'zone_1'
		zone_config = {
			'management': {
				'servers': SanityTestConfig.ManagementServers[0],
				'ws_port': 6123
			}
		}

		topology = Topology()
		topology.add_zone_config(zone_name, zone_config)
		fetcher = TopologyFetcher(topology=topology)

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
		topology.add_zone_config(zone_name, zone_config)
		fetcher = TopologyFetcher(topology=topology)

		with self.assertRaises(FailedToConnect):
			fetcher.listen_on_node_changes_on_zone(zone_name, zone_config)
