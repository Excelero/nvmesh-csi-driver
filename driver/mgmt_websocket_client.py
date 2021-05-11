#!/usr/bin/python

import json
import logging
import sys
import websocket
import ssl
from socket import error as socket_error

sslopt = {"cert_reqs": ssl.CERT_NONE}

logger = logging.getLogger('mgmt-ws-client')
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.DEBUG)


class EmptyResponseFromServer(Exception):
	pass

class FailedToConnect(Exception):
	pass

class LoginFailed(Exception):
	pass

class ManagementWebSocketClient(object):
	def __init__(self, servers_list, secure=True, client_id='python-ws-client'):
		self.client_id = client_id
		self.servers_list = servers_list
		self.secure = secure
		self.selected_server = None
		self.url = None
		self.ws = websocket.WebSocket(sslopt=sslopt)
		self.accessToken = None

	def connect(self):
		servers_we_can_still_try = set(self.servers_list)

		while len(servers_we_can_still_try):
			try:
				self.selected_server = servers_we_can_still_try.pop()
				self.url = self._build_url()
				self.ws.connect(self.url)
				return
			except (websocket.WebSocketAddressException, socket_error) as ex:
				logger.warning('Failed to connect to %s. Error: %s' % (self.url, ex))

		raise FailedToConnect('Failed to connect to any of the servers in %s' % self.servers_list)

	def _build_url(self):
		protocol = 'wss' if self.secure else 'ws'
		return '{protocol}://{address_with_port}'.format(
			protocol=protocol,
			address_with_port=self.selected_server)

	def login(self, username='admin@excelero.com', password='admin'):
		login_msg = {
			'route': '/login',
			'email': username,
			'password': password,
		}

		self.send(login_msg)
		res = self.receive()
		if res.get('success'):
			logger.info('{} login successful'.format(self.url))
			self.accessToken = res.get('accessToken')
			return True

		raise LoginFailed('Failed to login to management server at %s with user %s' % (self.url, username))

	def register_to_events(self, events):
		register_to_events_msg = {
			'route': '/registerToEvents',
			'payload': {
				'events': events
			}
		}

		self.send(register_to_events_msg)

	def send(self, data):
		msg = self._build_message(data)
		josn_data = json.dumps(msg)
		self.ws.send(josn_data)

	def receive(self):
		result = self.ws.recv()
		if not result:
			raise EmptyResponseFromServer()

		return json.loads(result)

	def close(self):
		self.ws.close()

	def _build_message(self, data):
		msg = {
			'registrant': {
				'id': self.client_id,
				'type': 'python-ws-client'
			},
			'accessToken': self.accessToken
		}

		msg.update(data)
		return msg

if __name__ == '__main__':
	c = ManagementWebSocketClient(client_id='test-python-client', servers_list=['10.0.1.117:4001'])
	c.connect()
	c.login()

	events = [
		'newClientEvent',
		'clientRemovedEvent'
	]
	event = c.register_to_events(events)
	logger.info('EVENT: %s' % event.get('payload'))
