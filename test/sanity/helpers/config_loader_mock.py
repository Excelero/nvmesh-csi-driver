from driver import consts
from driver.config import Config, ConfigValidator
from test.sanity.helpers.sanity_test_config import load_test_config_file, SanityTestConfig

load_test_config_file()

DEFAULT_MOCK_CONFIG = {
	'NVMESH_BIN_PATH': '/tmp/csi-driver-sanity/',
	'MANAGEMENT_SERVERS': 'localhost:4000',
	'MANAGEMENT_PROTOCOL': "https",
	'MANAGEMENT_USERNAME': "admin",
	'MANAGEMENT_PASSWORD': "admin",
	'SOCKET_PATH': 'unix:///tmp/csi/csi.sock',
	'DRIVER_NAME': "sanity.driver.test",
	'ATTACH_IO_ENABLED_TIMEOUT': 5,
	'PRINT_STACK_TRACES': True,
	'DRIVER_VERSION': "0.0.0",
	'NVMESH_VERSION_INFO': None,
	'TOPOLOGY_TYPE': consts.TopologyType.SINGLE_ZONE_CLUSTER,
	'TOPOLOGY': None,
	'SDK_LOG_LEVEL': 'DEBUG',
	'KUBE_CLIENT_LOG_LEVEL': 'DEBUG',
	'ZONE_DISABLED_TIME_IN_SECONDS': 15,
	'TOPOLOGY_CONFIG_MAP_NAME': 'nvmesh-csi-topology',
	'CSI_CONFIG_MAP_NAME': 'nvmesh-csi-config'
}

class ConfigLoaderMock:
	def __init__(self, configOverrides=None):

		self.configDict = DEFAULT_MOCK_CONFIG

		if configOverrides:
			self.configDict.update(configOverrides)

	def load(self):

		for key in self.configDict.keys():
			setattr(Config, key, self.configDict[key])

		ConfigValidator().validate_and_set_topology()
