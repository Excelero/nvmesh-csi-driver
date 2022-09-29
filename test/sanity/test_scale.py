import json
import logging
import os

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from driver import config_map_api

from driver.csi.csi_pb2 import TopologyRequirement, Topology
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.setup_and_teardown import start_server

import driver.consts as Consts

from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning
from test.sanity.clients.controller_client import ControllerClient
from test.sanity.nvmesh_cluster_simulator.nvmesh_mgmt_sim import create_clusters, get_config_topology_from_cluster_list

GB = pow(1024, 3)
VOL_1_ID = "vol_1"
VOL_2_ID = "vol_2"
DEFAULT_TOPOLOGY = Topology(segments={Consts.TopologyKey.ZONE: 'A'})
DEFAULT_TOPOLOGY_REQUIREMENTS = TopologyRequirement(requisite=[DEFAULT_TOPOLOGY], preferred=[DEFAULT_TOPOLOGY])
TOPO_REQ_MULTIPLE_TOPOLOGIES = TopologyRequirement(
	requisite=[
		Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'C'})
	],
	preferred=[
		Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'C'})
	])

os.environ['DEVELOPMENT'] = 'TRUE'

log = logging.getLogger('SanityTests').getChild('TestMultiZoneAtScale')

class TestMultiZoneAtScale(TestCaseWithServerRunning):

	def _delete_topology_config_map_if_exists(self):
		config_map_api.init()
		try:
			config_map_api.delete('nvmesh-csi-topology')
		except:
			pass

	def _create_multiple_clusters(self, num_of_clusters, num_of_client_per_cluster):
		clusters = create_clusters(num_of_clusters=num_of_clusters, num_of_client_per_cluster=num_of_client_per_cluster)

		for cluster in clusters:
			cluster.start()

		log.debug('waiting for all clusters to start')
		for cluster in clusters:
			cluster.wait_until_is_alive()


		def stop_all():
			log.info('stopping all clusters')
			for cluster in clusters:
				cluster.stop()

		self.addCleanup(stop_all)

		return clusters

	def test_scale(self):

		os.environ['DEVELOPMENT'] = 'TRUE'

		self._delete_topology_config_map_if_exists()

		clusters = self._create_multiple_clusters(num_of_clusters=15, num_of_client_per_cluster=5)

		config_topology = get_config_topology_from_cluster_list(clusters)

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': config_topology,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'DEBUG'
		}
		import driver.config as Config
		Config.config_loader = ConfigLoaderMock(config)
		Config.config_loader.load()

		self._start_csi_controller(config)


		log.debug('Creating volumes')
		ctrl_client = ControllerClient()

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		expected_volumes = {}
		def create_volume_for_specific_zone(zone_name):
			log.debug('create_volume_for_specific_zone %s' % zone_name)
			allowed_zones = Topology(segments={Consts.TopologyKey.ZONE: zone_name})
			allowed_topologies = TopologyRequirement(requisite=[allowed_zones], preferred=[allowed_zones])

			response = ctrl_client.CreateVolume(
				name='vol_zone_%s' % zone_name,
				capacity_in_bytes=5 * GB,
				parameters=parameters,
				topology_requirements=allowed_topologies)

			volume_id = response.volume.volume_id
			self.assertTrue(volume_id)

			if not zone_name in expected_volumes:
				expected_volumes[zone_name] = []

			volume_id_without_zone = volume_id.split(':')[1]
			expected_volumes[zone_name].append(volume_id_without_zone)

		for cluster in clusters:
			create_volume_for_specific_zone(cluster.name)

		# Verify volumes created in the correct zones
		volumes_from_clusters = {}
		for cluster in clusters:
			# Fetch volumes from the mgmt server and compare
			mgmt_srv = cluster.get_mgmt_server_string()
			api = VolumeAPI(managementServers=mgmt_srv, managementProtocol='https')
			err, volumes = api.get()
			volume_ids = [v._id for v in volumes]
			volumes_from_clusters[cluster.name] = volume_ids

		for cluster in clusters:
			expected_volume_ids = expected_volumes[cluster.name]
			actual_volumes = volumes_from_clusters[cluster.name]
			self.assertItemsEqual(expected_volume_ids, actual_volumes, 'expected: {}\n\nfound: {}'.format(pretty_json(expected_volumes), pretty_json(volumes_from_clusters)))

		log.info('test finished successfully')

	def _start_csi_controller(self, config):
		log.debug('Starting CSI Controller')
		driver_server = start_server(Consts.DriverType.Controller, config=config)

		def stop_driver():
			log.debug('stopping driver')
			driver_server.stop()

		self.addCleanup(stop_driver)


def pretty_json(obj):
	return json.dumps(obj, indent=4, sort_keys=True)


