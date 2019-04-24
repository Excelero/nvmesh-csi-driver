from driver.common import DriverLogger

class BaseClient(object):
	def __init__(self):
		self.logger = DriverLogger(self.__class__.__name__)
