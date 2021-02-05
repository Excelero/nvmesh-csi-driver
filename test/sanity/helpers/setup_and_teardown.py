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
		return None

def set_environment():
	config.Config.NVMESH_BIN_PATH = '/tmp/'

def start_server(driverType, mock_node_id=None):
	driver_server = ServerManager(driverType, mock_node_id)
	driver_server.start()
	is_server_running()

	return driver_server