import json
import threading
import logging

from NVMeshSDK.APIs.ClientAPI import ClientAPI
from common import BackoffDelay
from mgmt_websocket_client import ManagementWebSocketClient, EmptyResponseFromServer, FailedToConnect

logger = logging.getLogger('topology-service')

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

	def on_change(self):
		for listener in self.on_change_listeners:
			listener()

	def add_zone_config(self, zone_name, zone):
		with self.lock:
			zone['nodes'] = set()
			self.zones[zone_name] = zone

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
		with self.lock:
			json_str = json.dumps(self.zones, cls=SetEncoder)

		return json.loads(json_str)

	def __str__(self):
		return self.get_serializable_topology()

class TopologyFetcher(object):
	def __init__(self, topology):
		self.topology = topology
		self.should_continue = True
		self.ws_clients = {}
		self.fetching_locks = {}
		self.ws_threads = []

	def fetch_and_listen_for_changes_on_all_zones(self):
		for zone_id, zone_config in self.topology.zones.items():
			t = threading.Thread(target=self.fetch_and_listen_for_changes_on_zone, args=(zone_id, zone_config))
			self.ws_threads.append(t)
			t.start()

	def fetch_and_listen_for_changes_on_zone(self, zone, zone_config):
		mgmt_address = zone_config.get('management').get('servers')
		logger.debug('Connecting to management for zone %s on servers %s ' % (zone, mgmt_address))

		backoff = BackoffDelay(initial_delay=5, factor=2, max_delay=300)
		while self.should_continue:
			try:
				self.listen_on_node_changes_on_zone(zone, zone_config)
			except EmptyResponseFromServer as ex:
				backoff.reset()
				if not self.should_continue:
					break
				logger.warning('Lost connection to management server %s. Error: %s. Waiting %d seconds before trying again' % (mgmt_address, ex, backoff.current_delay))
			except FailedToConnect as ex:
				logger.warning('Failed to connect to management %s on zone %s: %s. Waiting %d seconds before trying again' % (mgmt_address, zone, ex, backoff.current_delay))
			except Exception as ex:
				logger.exception(ex)
			finally:
				backoff.wait()

		logger.info('Stopped listening thread for zone %s management server %s.' % (zone, mgmt_address))

	def fetch_and_add_nodes_for_zone(self, zone_config, zone):
		management_info = zone_config.get('management')
		if zone not in self.fetching_locks:
			self.fetching_locks[zone] = threading.Lock()

		# non-blocking acquire - if already locked it will return False
		got_the_lock = self.fetching_locks[zone].acquire(False)
		if not got_the_lock:
			logger.debug('Fetching for zone %s on servers %s is already in progress' % (zone, management_info.get('servers')))
			return

		backoff = BackoffDelay(initial_delay=15, factor=2, max_delay=300)

		try:
			while self.should_continue:
				try:
					node_ids = self.fetch_nodes_from_management_server(management_info)
					self.topology.add_nodes_for_zone(zone, node_ids)
					return
				except Exception as ex:
					logger.warning('Error fetching nodes for zone {0} on servers {1}. Error: {2}. Waiting {3} seconds before trying again'.format(
						zone, management_info.get('servers'), ex, backoff.current_delay))
					backoff.wait()
		finally:
			self.fetching_locks[zone].release()

	def listen_on_node_changes_on_zone(self, zone, zone_config):
		mgmt_info = zone_config.get('management')
		api_params = self.get_api_params(mgmt_info)

		ws_addresses = self.get_ws_servers_list(mgmt_info)
		ws_client = ManagementWebSocketClient(client_id='csi-driver-topology-fetcher', servers_list=ws_addresses)
		ws_client.connect()
		ws_client.login(username=api_params.get('user'), password=api_params.get('password'))
		self.ws_clients[zone] = ws_client
		logger.debug('Listening on client changes for zone %s on servers %s ' % (zone, api_params['managementServers']))

		# send a message to request updates on client changes
		ws_client.register_to_events(['newClientEvent', 'clientRemovedEvent'])

		# before listening we will spawn a thread to fetch all clients
		self.fetch_nodes_for_zone_in_new_thread(zone, zone_config)

		while self.should_continue:
			res = ws_client.receive()
			if self.should_continue and res:
				self.on_event_received(res.get('payload'), zone)

	def on_event_received(self, event, zone):
		event_name = event.get('eventName')

		if event_name == 'newClientEvent':
			client_id = event['payload'].get('clientID')
			logger.info('Found new client %s on zone %s' % (client_id, zone))
			self.topology.add_nodes_for_zone(zone, [client_id])

		elif event_name == 'clientRemovedEvent':
			client_id = event['payload'].get('clientID')
			logger.info('Client %s removed from nvmesh-management on zone %s' % (client_id, zone))
			self.topology.remove_nodes_for_zone(zone, [client_id])

	def fetch_nodes_for_zone_in_new_thread(self, zone, zone_config):
		t = threading.Thread(target=self.fetch_and_add_nodes_for_zone, args=(zone_config, zone))
		t.start()

	def fetch_nodes_from_management_server(self, management_info):
		api_params = self.get_api_params(management_info)

		logger.debug('Creating API from servers %s ' % api_params['managementServers'])
		api = ClientAPI(logger=sdk_logger, **api_params)
		logger.debug('Fetching nodes from servers %s ' % api_params['managementServers'])
		err, results = api.get()
		if err:
			raise Exception(str(err))

		node_ids = [client.client_id for client in results]
		return list(node_ids)

	def get_api_params(self, management_info):
		protocol = management_info.get('protocol', 'https')
		managementServers = management_info.get('servers')
		user = management_info.get('username', 'admin@excelero.com')
		password = management_info.get('password', 'admin')

		return {
			'managementProtocol': protocol,
			'managementServers': managementServers,
			'user': user,
			'password': password
		}

	def stop(self):
		self.should_continue = False

		logger.debug('stop(): Closing all websocket connections')
		for ws in self.ws_clients.itervalues():
			ws.close()

		logger.debug('stop(): Waiting for all websocket threads to finish')
		for t in self.ws_threads:
			t.join()

		logger.debug('stop(): All websocket threads to finished')

	def get_ws_servers_list(self, mgmt_info):
		ws_port = mgmt_info.get('ws_port', 4001)
		address_with_gui_port = mgmt_info.get('servers')
		ws_addresses = []

		for address in address_with_gui_port.split(','):
			ws_address = '{}:{}'.format(address.split(':')[0], ws_port)
			ws_addresses.append(ws_address)

		return ws_addresses





