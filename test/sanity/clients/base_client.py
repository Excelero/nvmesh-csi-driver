import logging

import grpc

from driver.config import Config
from test.sanity.clients.client_logging_interceptor import ClientLoggingInterceptor

sanity_logger = logging.getLogger('SanityTests')

class BaseClient(object):
	def __init__(self, socket_path=None):
		self.logger = sanity_logger.getChild(self.__class__.__name__)
		self.channel = grpc.insecure_channel(socket_path or Config.SOCKET_PATH)
		self.intercepted_channel = grpc.intercept_channel(self.channel, ClientLoggingInterceptor(self.logger))

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()