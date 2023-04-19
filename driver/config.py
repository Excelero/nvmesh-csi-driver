import json
import os

import consts as Consts

CONFIG_PATH = '/config'
NVMESH_VERSION_FILE_PATH = '/opt/NVMesh/client-repo/version'
DRIVER_VERSION_FILE_PATH = '/version'

class ConfigError(Exception):
	pass

class Config(object):
	NVMESH_BIN_PATH = None
	MANAGEMENT_SERVERS = None
	MANAGEMENT_PROTOCOL = None
	MANAGEMENT_USERNAME = None
	MANAGEMENT_PASSWORD = None
	SOCKET_PATH = None
	DRIVER_NAME = None
	ATTACH_IO_ENABLED_TIMEOUT = None
	PRINT_STACK_TRACES = None
	DRIVER_VERSION = None
	NVMESH_VERSION_INFO = None
	TOPOLOGY_TYPE = None
	TOPOLOGY = None
	LOG_LEVEL = None
	SDK_LOG_LEVEL = None
	KUBE_CLIENT_LOG_LEVEL = None
	ZONE_MAX_DISABLED_TIME_IN_SECONDS = None
	TOPOLOGY_CONFIG_MAP_NAME = None
	CSI_CONFIG_MAP_NAME = None
	USE_PREEMPT = None
	SDK_HTTP_REQUEST_TIMEOUT = None
	GRPC_MAX_WORKERS = None


class Parsers(object):
	@staticmethod
	def parse_boolean(stringValue):
		if stringValue.lower() == 'true':
			return True
		elif stringValue.lower() == 'false':
			return False
		else:
			raise ValueError('Could not parse boolean from {}'.format(stringValue))


def _read_file_contents(filename):
	with open(filename) as fp:
		return fp.read()

def _get_boolean_config_map_param(param_name):
	return _get_config_map_param(param_name, '').lower() == 'true'

def _get_config_map_param(name, default=None):
	value = None
	try:
		value = _read_file_contents(CONFIG_PATH + '/' + name)
	except IOError:
		pass

	return value or default

def _read_bash_file(filename):
	g = {}
	l = {}

	if os.path.exists(filename):
		execfile(filename, g, l)

	return l

def _get_env_var(key, default=None, parser=None):
	if key in os.environ:
		if parser:
			try:
				return parser(os.environ[key])
			except ValueError as ex:
				raise ConfigError('Error parsing value for {key}. Error: {msg}'.format(key=key, msg=ex.message))
		else:
			return os.environ[key]
	else:
		return default

def get_config_json():
	asDict = dict(vars(Config))
	params = {}
	for key in asDict.keys():
		if not key.startswith('_'):
			params[key] = asDict[key]
	return json.dumps(params, indent=4)

def print_config():
	config_json = get_config_json()
	print('Config=%s' % config_json)

class ConfigLoader(object):
	def load(self):
		Config.SOCKET_PATH = _get_env_var('SOCKET_PATH', default=Consts.DEFAULT_UDS_PATH)
		Config.DRIVER_NAME = _get_env_var('DRIVER_NAME', default=Consts.DEFAULT_DRIVER_NAME)

		Config.NVMESH_BIN_PATH = _get_env_var('NVMESH_BIN_PATH', default='/host/bin')
		Config.DRIVER_VERSION = _read_file_contents(DRIVER_VERSION_FILE_PATH)
		Config.NVMESH_VERSION_INFO = _read_bash_file(NVMESH_VERSION_FILE_PATH)

		Config.ATTACH_IO_ENABLED_TIMEOUT = int(_get_config_map_param('attachIOEnabledTimeout', default=30))
		Config.PRINT_STACK_TRACES = _get_boolean_config_map_param('printStackTraces')
		Config.TOPOLOGY = _get_config_map_param('topology', default=None)
		Config.LOG_LEVEL = _get_config_map_param('logLevel', default='DEBUG')
		Config.SDK_LOG_LEVEL = _get_config_map_param('sdkLogLevel', default='DEBUG')
		Config.KUBE_CLIENT_LOG_LEVEL = _get_config_map_param('kubeClientLogLevel', default='INFO')
		Config.ZONE_MAX_DISABLED_TIME_IN_SECONDS = _get_config_map_param('zoneMaxDisabledTimeInSeconds', 120)
		Config.TOPOLOGY_CONFIG_MAP_NAME = _get_config_map_param('topologyConfigMapName', 'nvmesh-csi-topology')
		Config.CSI_CONFIG_MAP_NAME = _get_config_map_param('csiConfigMapName', 'nvmesh-csi-config')
		Config.USE_PREEMPT = _get_boolean_config_map_param('usePreempt')
		Config.SDK_HTTP_REQUEST_TIMEOUT = _get_config_map_param('sdkHttpRequestTimeout', 30)
		Config.GRPC_MAX_WORKERS = _get_config_map_param('grpcMaxWorkers', 50)

		if not Config.TOPOLOGY:
			Config.MANAGEMENT_SERVERS = _get_config_map_param('management.servers') or _get_env_var('MANAGEMENT_SERVERS')
			Config.MANAGEMENT_PROTOCOL = _get_config_map_param('management.protocol') or _get_env_var('MANAGEMENT_PROTOCOL', default='https')
			Config.MANAGEMENT_USERNAME = _get_env_var('MANAGEMENT_USERNAME', default='admin@excelero.com')
			Config.MANAGEMENT_PASSWORD = _get_env_var('MANAGEMENT_PASSWORD', default='admin')

		ConfigValidator().validate()
		print("Loaded Config with SOCKET_PATH={}, MANAGEMENT_SERVERS={}, DRIVER_NAME={}".format(Config.SOCKET_PATH, Config.MANAGEMENT_SERVERS, Config.DRIVER_NAME))

class ConfigValidator(object):
	@staticmethod
	def validate():
		if Config.TOPOLOGY:
			if Config.MANAGEMENT_SERVERS:
				print("WARNING: MANAGEMENT_SERVERS env variable has no effect when multipleNVMeshBackends is set to True")
		else:
			if not Config.MANAGEMENT_SERVERS:
				raise ConfigError("MANAGEMENT_SERVERS environment variable not found or is empty")

		if Config.TOPOLOGY:
			try:
				Config.TOPOLOGY = json.loads(Config.TOPOLOGY)
			except ValueError as ex:
				raise ConfigError('Failed to parse config.topology. Error %s. originalValue:\n%s' % (ex, Config.TOPOLOGY))

		ConfigValidator.validate_and_set_topology()

	@staticmethod
	def validate_and_set_topology():
		if not Config.TOPOLOGY:
			Config.TOPOLOGY_TYPE = Consts.TopologyType.SINGLE_ZONE_CLUSTER
			return

		supportedTopologyTypes = [
			# The driver should handle each supported topology type in node_service.NodeGetInfo and controller_service.CreateVolume
			Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS
		]

		topology_conf = Config.TOPOLOGY
		Config.TOPOLOGY_TYPE = topology_conf.get('type', Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS)

		if Config.TOPOLOGY_TYPE not in supportedTopologyTypes:
			raise ConfigError('Unsupported topologyType %s' % Config.TOPOLOGY_TYPE)

		ConfigValidator.validate_topology_config(topology_conf)

	@staticmethod
	def validate_topology_config(topology_conf):
		if "zoneSelectionPolicy" not in topology_conf:
			topology_conf["zoneSelectionPolicy"] = Consts.ZoneSelectionPolicy.RANDOM

		if "zones" not in topology_conf:
			raise ConfigError('Missing "zones" key in ConfigMap.topology')

		zones = topology_conf["zones"]
		if not isinstance(zones, dict):
			raise ConfigError('Expected "zones" key in ConfigMap.topology to be a dict, but received %s' % type(zones))

		for zone_id, zone_config in zones.items():
			if "management" not in zone_config:
				raise ConfigError('Missing "management" key in ConfigMap.topology in zone %s' % type(zone_id))

			if "servers" not in zone_config["management"]:
				raise ConfigError('Missing "management.servers" key in ConfigMap.topology in zone %s' % type(zone_id))


config_loader = ConfigLoader()
