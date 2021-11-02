import os
import subprocess

from driver import consts
from driver.config import Config, ConfigValidator
from test.sanity.helpers.sanity_test_config import load_test_config_file

load_test_config_file()

def get_version_info():
	project_root = os.environ.get('PROJECT_ROOT', '../../')
	get_version_info_path = os.path.join(project_root, 'get_version_info.sh')
	version_info_output = subprocess.check_output(['/bin/bash', '-c', get_version_info_path])
	version_info = {}
	for line in version_info_output.split('\n'):
		if not line:
			continue
		key_value = line.split('=')
		version_info[key_value[0]] = key_value[1]

	return version_info


version_info = get_version_info()

DEFAULT_MOCK_CONFIG = {
	'NVMESH_BIN_PATH': '/tmp/csi-driver-sanity/',
	'MANAGEMENT_SERVERS': 'localhost:4000',
	'MANAGEMENT_PROTOCOL': "https",
	'MANAGEMENT_USERNAME': "admin",
	'MANAGEMENT_PASSWORD': "admin",
	'SOCKET_PATH': 'unix:///tmp/csi/csi.sock',
	'DRIVER_NAME': "nvmesh-csi.excelero.com",
	'ATTACH_IO_ENABLED_TIMEOUT': 5,
	'PRINT_STACK_TRACES': True,
	'DRIVER_VERSION': version_info['DRIVER_VERSION'],
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
