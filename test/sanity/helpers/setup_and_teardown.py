import sys
import time

from driver import config
from test.sanity.helpers import config_loader_mock

config.config_loader = config_loader_mock.ConfigLoaderMock()

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.server_manager import ServerManager

def is_server_running():
	try:
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		return msg.ready
	except Exception as ex:
		return False

def set_environment():
	config.Config.NVMESH_BIN_PATH = '/tmp/'

def wait_for_grpc_server_to_be_up():
	attempts = 15
	print('waiting for gRPC server to be available')
	while not is_server_running() and attempts > 0:
		attempts = attempts - 1
		print('waiting for gRPC server to be available..')
		time.sleep(1)


def start_server(driverType, mock_node_id=None):
	driver_server = ServerManager(driverType, mock_node_id)
	driver_server.start()
	wait_for_grpc_server_to_be_up()
	return driver_server

