import threading
import logging

from websocket import WebSocketConnectionClosedException

from NVMeshSDK.APIs.ClientAPI import ClientAPI
from NVMeshSDK.MongoObj import MongoObj
from common import BackoffDelayWithStopEvent
from config import Config
from mgmt_websocket_client import ManagementWebSocketClient, EmptyResponseFromServer, FailedToConnect, LoginFailed

logger = logging.getLogger('topology-service')

sdk_logger = logging.getLogger('NVMeshSDK')

class ZoneTopologyFetcherThread(threading.Thread):
	'''
	This Class runs as a thread and is in-charge of updating at run-time the list of nodes for a specific zone
	On run() the thread will do initial fetching of all clients from a zone
	And then open a WebSocket connection to the management and listen for client changes
	'''
	def __init__(self, zone_id, zone_config, topology, stop_event):
		self.zone_id = zone_id
		self.zone_config = zone_config
		self.topology = topology
		self.stop_event = threading.Event()
		self.ws_client = None
		self.ws_thread = None
		self.fetching_lock = threading.Lock()
		self.logger = logger.getChild('ZoneListeningThread(%s)' % self.zone_id)
		threading.Thread.__init__(self)
		self.name = 'zone-topology-fetcher-thread'

	def run(self):
		self.fetch_and_listen_for_changes_on_zone(self.zone_id, self.zone_config)
		self.logger.info('Thread for zone %s Stopped.' % self.zone_id)

	def stop(self):
		self.stop_event.set()
		self.logger.debug('Closing websocket connection..')
		self.ws_client.close()
		self.logger.debug('Websocket connection closed.')

	def fetch_and_listen_for_changes_on_zone(self, zone, zone_config):
		mgmt_address = zone_config.get('management').get('servers')
		self.logger.debug('Connecting to management on servers %s ' % mgmt_address)

		backoff = BackoffDelayWithStopEvent(self.stop_event, initial_delay=5, factor=2, max_delay=Config.ZONE_MAX_DISABLED_TIME_IN_SECONDS)
		while not self.stop_event.is_set():
			try:
				self.listen_on_node_changes_on_zone(zone, zone_config)
			except (EmptyResponseFromServer, WebSocketConnectionClosedException) as ex:
				backoff.reset()
				if self.stop_event.is_set():
					break
				self.logger.warning('Lost connection to management server %s. Error: %s. Waiting %d seconds before trying again' % (mgmt_address, ex, backoff.current_delay))
			except (FailedToConnect, LoginFailed) as ex:
				self.logger.warning('Failed to connect to management %s on zone %s: %s. Waiting %d seconds before trying again' % (mgmt_address, zone, ex, backoff.current_delay))
			except Exception as ex:
				self.logger.exception(ex)
			finally:
				self.topology.disable_zone(zone)
				backoff.wait()

		self.logger.info('Stopped listening thread for management server %s.' % mgmt_address)

	def listen_on_node_changes_on_zone(self, zone, zone_config):
		mgmt_info = zone_config.get('management')
		api_params = self.get_api_params(mgmt_info)

		ws_addresses = self.get_ws_servers_list(mgmt_info)
		ssl = api_params.get('managementProtocol') == 'https'
		self.ws_client = ManagementWebSocketClient(client_id='csi-driver-topology-fetcher', servers_list=ws_addresses, ssl=ssl)
		self.ws_client.connect()
		self.ws_client.login(username=api_params.get('user'), password=api_params.get('password'))

		self.topology.make_sure_zone_enabled(zone)
		self.logger.debug('Listening for client changes on servers %s ' % (api_params['managementServers']))

		# send a message to request updates on client changes
		self.ws_client.register_to_events(['newClientEvent', 'clientRemovedEvent'])

		# before listening we will spawn a thread to fetch all clients
		self.fetch_nodes_for_zone_in_new_thread(zone, zone_config)

		while not self.stop_event.is_set():
			res = self.ws_client.receive()
			if not self.stop_event.is_set() and res:
				self.on_event_received(res.get('payload'), zone)

	def fetch_and_add_nodes_for_zone(self, zone_config, zone):
		management_info = zone_config.get('management')

		# non-blocking acquire - if already locked it will return False
		got_the_lock = self.fetching_lock.acquire(False)
		if not got_the_lock:
			self.logger.debug('Fetching for zone %s on servers %s is already in progress' % (zone, management_info.get('servers')))
			return

		backoff = BackoffDelayWithStopEvent(self.stop_event, initial_delay=15, factor=2, max_delay=300)

		try:
			while not self.stop_event.is_set():
				try:
					node_ids = self.fetch_nodes_from_management_server(management_info)
					self.topology.add_nodes_for_zone(zone, node_ids)
					return
				except Exception as ex:
					self.logger.warning('Error fetching nodes for zone {0} on servers {1}. Error: {2}. Waiting {3} seconds before trying again'.format(
						zone, management_info.get('servers'), ex, backoff.current_delay))
					backoff.wait()
		finally:
			self.fetching_lock.release()

	def fetch_nodes_for_zone_in_new_thread(self, zone, zone_config):
		t = threading.Thread(target=self.fetch_and_add_nodes_for_zone, args=(zone_config, zone))
		t.start()

	def fetch_nodes_from_management_server(self, management_info):
		api_params = self.get_api_params(management_info)

		self.logger.debug('Creating API from servers %s ' % api_params['managementServers'])
		api = ClientAPI(**api_params)
		self.logger.debug('Fetching nodes from servers %s ' % api_params['managementServers'])
		projection = [
			MongoObj(field='client_id', value=1), 
			MongoObj(field='client_status', value=1)
		]

		err, results = api.get(projection=projection)
		if err:
			raise Exception(str(err))

		node_ids = [client.client_id for client in results]
		return list(node_ids)

	def get_ws_servers_list(self, mgmt_info):
		ws_port = mgmt_info.get('ws_port', 4001)
		address_with_gui_port = mgmt_info.get('servers')
		ws_addresses = []

		for address in address_with_gui_port.split(','):
			ws_address = '{}:{}'.format(address.split(':')[0], ws_port)
			ws_addresses.append(ws_address)

		return ws_addresses

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

	def on_event_received(self, event, zone):
		event_name = event.get('eventName')

		if event_name == 'newClientEvent':
			client_id = event['payload'].get('clientID')
			self.logger.info('Found new client %s on zone %s' % (client_id, zone))
			self.topology.add_nodes_for_zone(zone, [client_id])

		elif event_name == 'clientRemovedEvent':
			client_id = event['payload'].get('clientID')
			self.logger.info('Client %s removed from nvmesh-management on zone %s' % (client_id, zone))
			self.topology.remove_nodes_for_zone(zone, [client_id])
