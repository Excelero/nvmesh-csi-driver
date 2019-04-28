import yaml
import os

from driver.common import Consts, DriverLogger

logger = DriverLogger()

Config = None

class ConfigIsReadOnly(Exception):
	pass

class ConfigClass(object):
	def __init__(self, dictionary):
		self._loaded = False
		for k, v in dictionary.items():
			if isinstance(v, dict):
				v = ConfigClass(v)
			setattr(self, k, v)
		self._loaded = True

	def __setattr__(self, key, value):
		if key.startswith('_') or not self._loaded:
			object.__setattr__(self, key, value)
		else:
			raise ConfigIsReadOnly('Attempt to set attribute {} with value {} but Config is readonly'.format(key, value))

	def __getattr__(self, key):
		if not key in self.__dict__:
			return EmptyConfigClass()
		else:
			return self.__dict__[key]

class EmptyConfigClass(ConfigClass):
	def __init__(self):
		ConfigClass.__init__(self, {})

	def __nonzero__(self):
		return False

class ConfigLoader(object):

	@staticmethod
	def load():
		filepath = Consts.CONFIG_FILE_PATH
		if 'CONFIG_FILE_PATH' in os.environ and os.environ['CONFIG_FILE_PATH']:
			filepath = os.environ['CONFIG_FILE_PATH']
			logger.debug("CONFIG_FILE_PATH env var found, using filepath {}".format(filepath))
		return ConfigLoader._load_from_file(filepath)

	@staticmethod
	def _load_from_file(filepath):
		global Config
		data = None
		with open(filepath, 'r') as f:
			try:
				data = yaml.safe_load(f)
				Config = ConfigClass(data)
			except yaml.YAMLError as ex:
				logger.error('Error reading Config file at {0} file. err: {1}'.format(filepath, ex.message))
				raise ex

		return data


ConfigLoader.load()
