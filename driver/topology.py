import json
import threading
import logging

logger = logging.getLogger('topology')

sdk_logger = logging.getLogger('NVMeshSDK')
sdk_logger.setLevel(logging.DEBUG)

class SetEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, set):
			return list(obj)
		return json.JSONEncoder.default(self, obj)

class Topology(object):
	def __init__(self):
		self.lock = threading.Lock()
		self.nodes = {}
		self.zones = {}
		self.on_change_listeners = []
		self.disabled_zones_lock = threading.Lock()
		self.temp_disabled_zones = {}

	def on_change(self):
		for listener in self.on_change_listeners:
			listener()

	def set_zone_config_without_lock(self, zone_name, zone_config):
		zone_config['nodes'] = set()
		self.zones[zone_name] = zone_config

	def add_nodes_for_zone(self, zone, node_ids):
		with self.lock:
			for node_id in node_ids:
				old_zone = self.nodes.get(node_id)
				if old_zone != zone:
					self.nodes[node_id] = zone
					self.zones[zone]['nodes'].add(node_id)

					if old_zone:
						self.zones[old_zone]['nodes'].remove(node_id)
						logger.info('Node {} moved from zone {} to zone {}'.format(node_id, old_zone, zone))
					else:
						logger.info('Node {} added to zone {}'.format(node_id, zone))
		self.on_change()

	def remove_zone(self, zone):
		nodes = self.zones[zone]['nodes']
		for node_id in nodes:
			if self.nodes[node_id] == zone:
				self.nodes.pop(node_id, None)

		del self.zones[zone]
		logger.info('Zone {} with {} nodes was removed'.format(zone, len(nodes)))
		self.on_change()

	def remove_nodes_for_zone(self, zone, node_ids):
		with self.lock:
			for node_id in node_ids:
				if self.nodes.get(node_id) == zone:
					del self.nodes[node_id]
					logger.info('Node {} removed from zone {}'.format(node_id, zone))

				self.zones[zone]['nodes'].discard(node_id)

		self.on_change()

	def get_zone_for_node_id(self, node_id):
		# Could return None
		with self.lock:
			zone = self.nodes.get(node_id)

		return zone

	def get_serializable_topology(self):
		json_str = json.dumps(self.zones, cls=SetEncoder)
		return json.loads(json_str)

	def disable_zone(self, zone):
		with self.disabled_zones_lock:
			logger.warning('disabled_zones: zone {} disabled'.format(zone))
			self.temp_disabled_zones[zone] = {}

	def make_sure_zone_enabled(self, zone):
		with self.disabled_zones_lock:
			if zone in self.temp_disabled_zones:
				logger.info('disabled_zones: zone {} enabled'.format(zone))
				del self.temp_disabled_zones[zone]

	def is_zone_disabled(self, zone):
		with self.disabled_zones_lock:
			return zone in self.temp_disabled_zones.keys()

	def __str__(self):
		return self.get_serializable_topology()
