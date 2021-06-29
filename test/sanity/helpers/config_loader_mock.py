import socket

from driver import consts
from driver.config import Config, ConfigValidator
from test.sanity.helpers.sanity_test_config import load_test_config_file, SanityTestConfig

load_test_config_file()
ACTIVE_MANAGEMENT_SERVER = SanityTestConfig.ManagementServers[0]

DEFAULT_CONFIG_TOPOLOGY = {
					"zones": {
							"A": {
								"management": {
									"servers": SanityTestConfig.ManagementServers[0]
								}
							},
							"B": {
								"management": {
									"servers": SanityTestConfig.ManagementServers[1]
								}
							},
							"C": {
								"management": {
									"servers": SanityTestConfig.ManagementServers[1]
								}
							},
						}
					}

DEFAULT_MOCK_CONFIG = {
	'NVMESH_BIN_PATH': '/tmp/csi-driver-sanity/',
	'MANAGEMENT_SERVERS': ACTIVE_MANAGEMENT_SERVER,
	'MANAGEMENT_PROTOCOL': "https",
	'MANAGEMENT_USERNAME': "admin",
	'MANAGEMENT_PASSWORD': "admin",
	'SOCKET_PATH': 'unix:///tmp/test.sock',
	'DRIVER_NAME': "sanity.driver.test",
	'ATTACH_IO_ENABLED_TIMEOUT': 5,
	'PRINT_STACK_TRACES': True,
	'DRIVER_VERSION': "0.0.0",
	'NVMESH_VERSION_INFO': None,
	'TOPOLOGY_TYPE': consts.TopologyType.SINGLE_ZONE_CLUSTER,
	'TOPOLOGY': DEFAULT_CONFIG_TOPOLOGY,
	'SDK_LOG_LEVEL': 'DEBUG',
	'KUBE_CLIENT_LOG_LEVEL': 'DEBUG',
	'ZONE_DISABLED_TIME_IN_SECONDS': 15
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
