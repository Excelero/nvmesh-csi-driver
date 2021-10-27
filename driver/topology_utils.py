import Queue
import json
import logging
import random
import threading

from grpc import StatusCode

import consts
from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.ConnectionManager import ConnectionManager
from common import DriverError
from config import Config

logger = logging.getLogger('topology-service')

class NodeNotFoundInTopology(Exception):
	pass

class TopologyUtils(object):
	@staticmethod
	def get_zone_info(zone):
		zone_info = Config.TOPOLOGY['zones'].get(zone)

		if not zone_info:
			raise ValueError('Zone %s missing from Config.topology' % zone)

		return zone_info

	@staticmethod
	def get_management_info_from_zone(zone):
		logger.debug('get_management_info_from_zone for zone {}'.format(zone))
		zone_info = TopologyUtils.get_zone_info(zone)
		logger.debug('get_management_info_from_zone zone_info {}'.format(zone_info))

		mgmt_info = zone_info.get('management')
		logger.debug('get_management_info_from_zone mgmt_info {}'.format(mgmt_info))

		if not mgmt_info:
			raise ValueError('Zone {0} missing mgmt_info in Config.topology.zones.{0}'.format(zone))

		return mgmt_info

	@staticmethod
	def get_node_zone(node_id):
		with open(consts.NODE_DRIVER_TOPOLOGY_PATH) as fp:
			zones = json.load(fp)
			for zone_name, zone_data in zones.iteritems():
				nodes = zone_data['nodes']
				if node_id in nodes:
					return zone_name

		raise NodeNotFoundInTopology()

	@staticmethod
	def get_all_zones_from_topology():
		cluster_topology = Config.TOPOLOGY
		return cluster_topology.get('zones').keys()

	@staticmethod
	def get_topology_key():
		if not Config.TOPOLOGY:
			return consts.TopologyKey.ZONE

		return Config.TOPOLOGY.get('topologyKey', consts.TopologyKey.ZONE)

	@staticmethod
	def get_allowed_zones_from_topology(topology_requirements):
		if Config.TOPOLOGY_TYPE == consts.TopologyType.SINGLE_ZONE_CLUSTER:
			return [consts.SINGLE_CLUSTER_ZONE_NAME]

		# provisioner sidecar container should have --strict-topology flag set
		# If volumeBindingMode is Immediate - all cluster topology will be received
		# If volumeBindingMode is WaitForFirstConsumer - Only the topology of the node to which the pod is scheduled will be given
		try:
			topology_key = TopologyUtils.get_topology_key()
			preferred_topologies = topology_requirements.get('preferred')
			zones = map(lambda t: t['segments'][topology_key], preferred_topologies)
			return zones
		except Exception as ex:
			raise ValueError('Failed to get zone from topology. Error: %s' % ex)

	@staticmethod
	def get_zone_from_topology(logger, topology_requirements):
		if Config.TOPOLOGY_TYPE == consts.TopologyType.SINGLE_ZONE_CLUSTER:
			return consts.SINGLE_CLUSTER_ZONE_NAME

		# provisioner sidecar container should have --strict-topology flag set
		# If volumeBindingMode is Immediate - all cluster topology will be received
		# If volumeBindingMode is WaitForFirstConsumer - Only the topology of the node to which the pod is scheduled will be given
		try:
			topology_key = TopologyUtils.get_topology_key()
			preferred_topologies = topology_requirements.get('preferred')
			if len(preferred_topologies) == 1:
				selected_zone = preferred_topologies[0]['segments'][topology_key]
			else:
				zones = map(lambda t: t['segments'][topology_key], preferred_topologies)
				selected_zone = ZoneSelectionManager.pick_zone(zones)
		except Exception as ex:
			raise ValueError('Failed to get zone from topology. Error: %s' % ex)

		if not selected_zone:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Failed to get zone from topology')

		logger.debug('_get_zone_from_topology selected zone is {}'.format(selected_zone))
		return selected_zone

	@staticmethod
	def get_api_params_from_config():
		return {
			'managementServers': Config.MANAGEMENT_SERVERS,
			'managementProtocol': Config.MANAGEMENT_PROTOCOL,
			'user': Config.MANAGEMENT_USERNAME,
			'password': Config.MANAGEMENT_PASSWORD
		}

	@staticmethod
	def get_api_params(zone):
		logger.debug('get_api_params for zone {}'.format(zone))
		if Config.TOPOLOGY_TYPE == consts.TopologyType.SINGLE_ZONE_CLUSTER:
			return TopologyUtils.get_api_params_from_config()

		mgmt_info = TopologyUtils.get_management_info_from_zone(zone)

		if not mgmt_info:
			raise ValueError('Missing "management" key in Config.topology.zones.%s' % zone)

		managementServers = mgmt_info.get('servers')
		if not managementServers:
			raise ValueError('Missing "servers" key in Config.topology.zones.%s.management ' % zone)

		api_params = {
			'managementServers': managementServers
		}

		user = mgmt_info.get('user')
		password = mgmt_info.get('password')
		protocol = mgmt_info.get('protocol')

		if user:
			api_params['user'] = user

		if password:
			api_params['password'] = password

		if protocol:
			api_params['managementProtocol'] = protocol

		return api_params


class VolumeAPIPool(object):
	__lock = threading.Lock()
	__api_dict = {}


	@staticmethod
	def get_volume_api_for_zone(zone, log):
		api_params = TopologyUtils.get_api_params(zone)
		management_servers = api_params['managementServers']
		with VolumeAPIPool.__lock:
			log.debug('get_volume_api_for_zone: management_servers=%s' % management_servers)
			if management_servers in VolumeAPIPool.__api_dict:
				api = VolumeAPIPool.__api_dict[management_servers]
				log.debug('get_volume_api_for_zone: got VolumeAPI object from pool with mgmts: %s' % api.managementConnection.managementServers)
			else:
				api = VolumeAPIPool._create_new_volume_api(api_params)
				VolumeAPIPool.__api_dict[management_servers] = api
				log.debug('get_volume_api_for_zone: created new VolumeAPI=%s from api_params %s' % (api.managementConnection.managementServers, api_params))
				first_mgmt_server_from_api_params = 'https://' + api_params['managementServers'].split(',')[0]
				log.debug('first_mgmt_server_from_api_params: {}'.format(first_mgmt_server_from_api_params))
				if api.managementConnection.managementServers[0] != first_mgmt_server_from_api_params:
					# This means we asked for a connection to management server A but got a connection to management server B
					db_uuid_to_servers = ['db_uuid={} servers={}'.format(db_uuid, conn_mgr.managementServers) for db_uuid, conn_mgr in ConnectionManager.debug_getInstances().items()]
					log.debug('SDK internals: {}'.format(db_uuid_to_servers))
					raise ValueError('BUG! Got wrong API object! got Connection for {} but expected {}'.format(api.managementConnection.managementServers[0], 'https://' + api_params['managementServers']))

		return api

	@staticmethod
	def _create_new_volume_api(api_params):
		sdk_logger = logging.getLogger('NVMeshSDK')
		try:
			volume_api = VolumeAPI(logger=sdk_logger, **api_params)
			return volume_api
		except Exception as ex:
			sdk_logger.error('Failed to create VolumeAPI with params: {}. \nError {}'.format(api_params, ex))
			raise

	@staticmethod
	def isLocked():
		return VolumeAPIPool.__lock.locked()


class ZoneSelectionManager(object):
	_zone_picker = None

	@staticmethod
	def get_instance():
		if not ZoneSelectionManager._zone_picker:
			ZoneSelectionManager._zone_picker = ZoneSelectionManager._initialize_instance()

		return ZoneSelectionManager._zone_picker

	@staticmethod
	def _initialize_instance():
		topology = Config.TOPOLOGY or {}
		selection_policy = topology.get('zoneSelectionPolicy', consts.ZoneSelectionPolicy.RANDOM)
		if selection_policy == consts.ZoneSelectionPolicy.RANDOM:
			return RandomZonePicker()
		elif selection_policy == consts.ZoneSelectionPolicy.ROUND_ROBIN:
			return RoundRobinZonePicker()
		else:
			raise ValueError('Unknown zoneSelectionPolicy: %s ' % selection_policy)

	@staticmethod
	def pick_zone(zones):
		picker = ZoneSelectionManager.get_instance()
		return picker.pick_zone(zones)


class ZonePicker(object):
	def pick_zone(self, zones):
		raise ValueError('Not Implemented')


class RandomZonePicker(ZonePicker):
	def pick_zone(self, allowed_zones):
		zone = random.choice(allowed_zones)
		return zone


class RoundRobinZonePicker(ZonePicker):

	def __init__(self):
		self.zones_queue = Queue.Queue()
		self._build_queue()

	def _build_queue(self):
		topology_config = Config.TOPOLOGY
		for zone in topology_config.get('zones').keys():
			self.zones_queue.put(zone)

	def pick_zone(self, _unused):
		zone = self.zones_queue.get()
		self.zones_queue.put(zone)
		return zone


