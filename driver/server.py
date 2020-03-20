import grpc
import time
import signal

import sys, os
from concurrent import futures
from common import ServerLoggingInterceptor, DriverLogger
import consts as Consts
from controller_service import NVMeshControllerService
from csi import csi_pb2_grpc
from config import Config
from identity_service import NVMeshIdentityService
from node_service import NVMeshNodeService

def log(msg):
	print(msg)
	sys.stdout.flush()

class NVMeshCSIDriverServer(object):
	def __init__(self, driver_type):
		self.driver_type = driver_type
		self.logger = DriverLogger()
		self.identity_service = NVMeshIdentityService(self.logger)

		if self.driver_type == Consts.DriverType.Controller:
			self.controller_service = NVMeshControllerService(self.logger)
		else:
			self.node_service = NVMeshNodeService(self.logger)

		self.server = None
		self.shouldContinue = True
		self.logger.info("NVMesh CSI Driver Type: {} Version: {}".format(self.driver_type, Consts.DRIVER_VERSION))

	def serve(self):
		logging_interceptor = ServerLoggingInterceptor(self.logger)
		self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),interceptors=(logging_interceptor,))
		csi_pb2_grpc.add_IdentityServicer_to_server(self.identity_service, self.server)

		if self.driver_type == Consts.DriverType.Controller:
			csi_pb2_grpc.add_ControllerServicer_to_server(self.controller_service, self.server)
		else:
			csi_pb2_grpc.add_NodeServicer_to_server(self.node_service, self.server)

		self.server.add_insecure_port(Config.SOCKET_PATH)

		self.server.start()
		self.logger.info("Server is listening on {}".format(Config.SOCKET_PATH))
		self.wait_forever()

	def wait_forever(self):
		try:
			while self.shouldContinue:
				time.sleep(1)

			self.logger.info("Server Stopped")
		except KeyboardInterrupt:
			self.server.stop(0)

	def stop(self):
		self.logger.info("Server is Shutting Down..")
		self.shouldContinue = False
		self.server.stop(0)

def get_driver_type():
	if not 'DRIVER_TYPE' in os.environ:
		log("Could not find DRIVER_TYPE in environment Variables. Expected DRIVER_TYPE=Controller|Node")
		exit(1)

	driver_type = os.environ['DRIVER_TYPE']

	if driver_type != Consts.DriverType.Controller and driver_type != Consts.DriverType.Node:
		log("Unknown DRIVER_TYPE={}. Expected DRIVER_TYPE=Controller|Node".format(driver_type))
		exit(1)

	return driver_type

if __name__ == '__main__':
	driver_type = get_driver_type()
	driver = NVMeshCSIDriverServer(driver_type)

	def sigterm_handler(signum, frame):
		driver.stop()

	signal.signal(signal.SIGTERM, sigterm_handler)
	signal.signal(signal.SIGINT, sigterm_handler)

	driver.serve()
	driver.logger.info("Server Process Finished")
