import grpc

from driver.common import DriverLogger
from driver.config import Config
from test.clients.client_logging_interceptor import ClientLoggingInterceptor


class BaseClient(object):
	def __init__(self):
		self.logger = DriverLogger(self.__class__.__name__)
		self.channel = grpc.insecure_channel(Config.SOCKET_PATH)
		self.intercepted_channel = grpc.intercept_channel(self.channel, ClientLoggingInterceptor(self.logger))

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()