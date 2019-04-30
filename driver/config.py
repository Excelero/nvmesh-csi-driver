import os

from driver.common import Consts


class Config(object):
	MANAGEMENT_SERVERS = None
	MANAGEMENT_PROTOCOL = None
	MANAGEMENT_USERNAME = None
	MANAGEMENT_PASSWORD = None
	SOCKET_PATH = None

def _get_env_var_or_default(key, defaultValue):
	if key in os.environ:
		return os.environ[key]
	else:
		return defaultValue

def load():
	Config.MANAGEMENT_SERVERS = _get_env_var_or_default('MANAGEMENT_SERVERS', '')
	Config.MANAGEMENT_PROTOCOL = _get_env_var_or_default('MANAGEMENT_PROTOCOL', 'https')
	Config.MANAGEMENT_USERNAME = _get_env_var_or_default('MANAGEMENT_USERNAME', 'admin@excelero.com')
	Config.MANAGEMENT_PASSWORD = _get_env_var_or_default('MANAGEMENT_PASSWORD', 'admin')
	Config.SOCKET_PATH = _get_env_var_or_default('MANAGEMENT_PASSWORD', Consts.DEFAULT_UDS_PATH)

	print("Loaded Config with SOCKET_PATH={} ,MANAGEMENT_SERVERS = {}".format(Config.SOCKET_PATH, Config.MANAGEMENT_SERVERS))

load()