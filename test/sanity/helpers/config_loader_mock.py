from driver.config import Config

ACTIVE_MANAGEMENT_SERVER = "n117:4000"
class ConfigLoaderMock:
	def load(self):
		Config.NVMESH_BIN_PATH = '/tmp/csi-driver-sanity/'
		Config.MANAGEMENT_SERVERS = ACTIVE_MANAGEMENT_SERVER
		Config.MANAGEMENT_PROTOCOL = "https"
		Config.MANAGEMENT_USERNAME = "admin"
		Config.MANAGEMENT_PASSWORD = "admin"
		Config.SOCKET_PATH = 'unix:///tmp/test.sock'
		Config.DRIVER_NAME = "sanity.driver.test"
		Config.ATTACH_IO_ENABLED_TIMEOUT = 5
		Config.PRINT_TRACEBACKS = None
		Config.DRIVER_VERSION = "0.0.0"
		Config.NVMESH_VERSION_INFO = None

