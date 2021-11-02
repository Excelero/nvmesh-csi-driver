import logging
import time

from driver import config
from test.sanity.helpers import config_loader_mock
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.container_server_manager import ContainerServerManager

config.config_loader = config_loader_mock.ConfigLoaderMock()

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.server_manager import ServerManager

log = logging.getLogger('SanityTests')

def is_server_running():
	try:
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		return msg.ready
	except Exception as ex:
		return False


def wait_for_grpc_server_to_be_up():
	attempts = 15
	log.info('waiting for gRPC server to be available')
	while not is_server_running() and attempts > 0:
		attempts = attempts - 1
		log.info('waiting for gRPC server to be available..')
		time.sleep(1)


def start_server(driverType, config, mock_node_id=None, wait_for_grpc=True):
	ConfigLoaderMock(config).load()
	driver_server = ServerManager(driverType, config=config, mock_node_id=mock_node_id)
	driver_server.start()
	if wait_for_grpc:
		wait_for_grpc_server_to_be_up()
	return driver_server


def start_containerized_server(driver_type, config, hostname=None):
	ConfigLoaderMock(config).load()
	driver_server = ContainerServerManager(driver_type, config, node_id=hostname)
	driver_server.start()
	driver_server.wait_for_grpc_server_to_be_alive()
	return driver_server
