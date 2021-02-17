import socket

from driver import consts
from driver.config import Config, ConfigValidator

ACTIVE_MANAGEMENT_SERVER = "n117:4000"

DEFAULT_CONFIG_TOPOLOGY = {
					"zones": {
							"A": {
								"nodes": [socket.gethostname()],
								"management": {
									"servers": ACTIVE_MANAGEMENT_SERVER
								}
							},
							"B": {
								"nodes": ["nvme115.excelero.com"],
								"management": {
									"servers": "nvme117.excelero.com:4000"
								}
							},
							"C": {
								"nodes": ["nvme127.excelero.com"],
								"management": {
									"servers": "10.0.1.117:4000"
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
	'PRINT_STACK_TRACES': None,
	'DRIVER_VERSION': "0.0.0",
	'NVMESH_VERSION_INFO':None,
	'TOPOLOGY_TYPE': consts.TopologyType.SINGLE_ZONE_CLUSTER,
	'TOPOLOGY': DEFAULT_CONFIG_TOPOLOGY
}
class ConfigLoaderMock:
	def __init__(self, configDict=None):

		self.configDict = DEFAULT_MOCK_CONFIG

		if configDict:
			self.configDict.update(configDict)

	def load(self):

		for key in self.configDict.keys():
			setattr(Config, key, self.configDict[key])

		ConfigValidator().validate_topology()

