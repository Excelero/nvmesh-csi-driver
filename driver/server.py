import grpc
import time
import signal

import os
from concurrent import futures

from common import Consts, ServerLoggingInterceptor, DriverLogger

from controller_service import NVMeshControllerService
from csi import csi_pb2_grpc
from driver.config import Config
from identity_service import NVMeshIdentityService
from node_service import NVMeshNodeService

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class NVMeshCSIDriverServer(object):
	def __init__(self):
		self.logger = DriverLogger()
		self.identity_service = NVMeshIdentityService(self.logger)
		self.controller_service = NVMeshControllerService(self.logger)
		self.node_service = NVMeshNodeService(self.logger)
		self.server = None
		self.shouldContinue = True

	def serve(self):
		logging_interceptor = ServerLoggingInterceptor(self.logger)
		self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),interceptors=(logging_interceptor,))
		csi_pb2_grpc.add_IdentityServicer_to_server(self.identity_service, self.server)
		csi_pb2_grpc.add_ControllerServicer_to_server(self.controller_service, self.server)
		csi_pb2_grpc.add_NodeServicer_to_server(self.node_service, self.server)
		self.server.add_insecure_port(Config.SOCKET_PATH)

		self.server.start()
		self.logger.info("Server Started!")
		self.wait_forever()

	def wait_forever(self):
		try:
			while self.shouldContinue:
				time.sleep(_ONE_DAY_IN_SECONDS)
				self.logger.info("Server Stopped!")
		except KeyboardInterrupt:
			self.server.stop(0)

	def stop(self):
		self.logger.info("Server is Shutting Down!")
		self.shouldContinue = False
		self.server.stop(0)

if __name__ == '__main__':
	driver = NVMeshCSIDriverServer()

	def sigterm_handler(signum, frame):
		driver.stop()

	signal.signal(signal.SIGTERM, sigterm_handler)
	signal.signal(signal.SIGINT, sigterm_handler)

	driver.serve()
	driver.logger.info("Server Process Finished")
