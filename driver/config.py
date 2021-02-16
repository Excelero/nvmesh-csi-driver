import json
import os

import consts as Consts


class ConfigError(Exception):
	pass

class Config(object):
	MANAGEMENT_SERVERS = None
	MANAGEMENT_PROTOCOL = None
	MANAGEMENT_USERNAME = None
	MANAGEMENT_PASSWORD = None
	SOCKET_PATH = None
	DRIVER_NAME = None
	ATTACH_IO_ENABLED_TIMEOUT = None
	PRINT_TRACEBACKS = None
	LOG_LEVEL = None

class Parsers(object):
	@staticmethod
	def parse_boolean(stringValue):
		if stringValue.lower() == 'true':
			return True
		elif stringValue.lower() == 'false':
			return False
		else:
			raise ValueError('Could not parse boolean from {}'.format(stringValue))

class ConfigLoader(object):
	@staticmethod
	def _get_env_var_or_default(key, default=None, parser=None):
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

	@staticmethod
	def _get_json_config():
		try:
			with open('/etc/config/config') as fp:
				jsonConfig = json.load(fp)
				return jsonConfig
		except Exception as ex:
			raise ConfigError('Error parsing json config. Error: {}'.format(ex.message))

	@staticmethod
	def load():
		Config.MANAGEMENT_SERVERS = ConfigLoader._get_env_var_or_default('MANAGEMENT_SERVERS', default='')
		Config.MANAGEMENT_PROTOCOL = ConfigLoader._get_env_var_or_default('MANAGEMENT_PROTOCOL', default='https')
		Config.MANAGEMENT_USERNAME = ConfigLoader._get_env_var_or_default('MANAGEMENT_USERNAME', default='admin@excelero.com')
		Config.MANAGEMENT_PASSWORD = ConfigLoader._get_env_var_or_default('MANAGEMENT_PASSWORD', default='admin')
		Config.SOCKET_PATH = ConfigLoader._get_env_var_or_default('SOCKET_PATH', default=Consts.DEFAULT_UDS_PATH)
		Config.DRIVER_NAME = ConfigLoader._get_env_var_or_default('DRIVER_NAME', default=Consts.DEFAULT_DRIVER_NAME)
		Config.LOG_LEVEL = ConfigLoader._get_env_var_or_default('LOG_LEVEL', default='DEBUG').upper()

		jsonConfig = ConfigLoader._get_json_config()
		Config.ATTACH_IO_ENABLED_TIMEOUT = jsonConfig.get('attach_io_enabled_timeout', 30)
		Config.PRINT_TRACEBACKS = jsonConfig.get('print_tracebacks', False)

		if not Config.MANAGEMENT_SERVERS:
			raise ConfigError("MANAGEMENT_SERVERS environment variable not found or is empty")

		print("Loaded Config with SOCKET_PATH={}, MANAGEMENT_SERVERS={}, DRIVER_NAME={}".format(Config.SOCKET_PATH, Config.MANAGEMENT_SERVERS, Config.DRIVER_NAME))


ConfigLoader.load()
