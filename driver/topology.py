import Queue
import random

from grpc import StatusCode

import consts
from common import DriverError
from config import Config


class TopologyUtils(object):
	@staticmethod
	def get_zone_info(zone):
		zone_info = Config.TOPOLOGY['zones'].get(zone)

		if not zone_info:
			raise ValueError('Zone %s missing from Config.topology' % zone)

		return zone_info

	@staticmethod
	def get_management_info_from_zone(zone):
		zone_info = TopologyUtils.get_zone_info(zone)

		mgmt_info = zone_info.get('management')
		if not mgmt_info:
			raise ValueError('Zone {0} missing mgmt_info in Config.topology.zones.{0}'.format(zone))

		return mgmt_info

	@staticmethod
	def get_node_zone_from_topology(node_id):
		cluster_topology = Config.TOPOLOGY
		for zone_name, zone_data in cluster_topology.get('zones').items():
			nodes = zone_data['nodes']
			if node_id in nodes:
				return zone_name

		raise DriverError(StatusCode.INTERNAL, 'Could not find node %s in any of the zones in config.topology')

	@staticmethod
	def get_all_zones_from_topology():
		cluster_topology = Config.TOPOLOGY
		return cluster_topology.get('zones').keys()


class ZoneSelectionManager(object):
	_zone_picker = None

	@staticmethod
	def get_instance():
		if not ZoneSelectionManager._zone_picker:
			ZoneSelectionManager._zone_picker = ZoneSelectionManager._initialize_instance()

		return ZoneSelectionManager._zone_picker

	@staticmethod
	def _initialize_instance():
		topology = Config.TOPOLOGY
		selection_policy = topology.get('zoneSelectionPolicy')
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
