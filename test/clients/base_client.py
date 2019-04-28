from driver.common import DriverLogger

class BaseClient(object):
	def __init__(self):
		self.channel = None
		self.logger = DriverLogger(self.__class__.__name__)

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()