import grpc
import time
import signal

import sys
from concurrent import futures
from common import ServerLoggingInterceptor, DriverLogger, Utils
from controller_service import NVMeshControllerService
from csi import csi_pb2_grpc
from config import Config
from identity_service import NVMeshIdentityService
from node_service import NVMeshNodeService
from NVMeshSDK.ConnectionManager import ConnectionManager, ManagementTimeout

def log(msg):
	print(msg)
	sys.stdout.flush()

def init_sdk():

	protocol = Config.MANAGEMENT_PROTOCOL
	managementServers = Config.MANAGEMENT_SERVERS
	user = Config.MANAGEMENT_USERNAME
	password = Config.MANAGEMENT_PASSWORD

	serversWithProtocol = ['{0}://{1}'.format(protocol, server) for server in managementServers.split(',')]

	return ConnectionManager.getInstance(managementServer=serversWithProtocol, user=user, password=password, logToSysLog=False)

def wait_for_connection_to_management():
	connected = False

	while not connected:
		try:
			init_sdk()
			connected = ConnectionManager.getInstance().isAlive()
		except ManagementTimeout as ex:
			log("Waiting for NVMesh Management server on {}".format(Config.MANAGEMENT_SERVERS))
			Utils.interruptable_sleep(10)

	print("Connected to NVMesh Management server on {}".format(ConnectionManager.getInstance().managementServer))

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

if __name__ == '__main__':
	wait_for_connection_to_management()
	driver = NVMeshCSIDriverServer()

	def sigterm_handler(signum, frame):
		driver.stop()

	signal.signal(signal.SIGTERM, sigterm_handler)
	signal.signal(signal.SIGINT, sigterm_handler)

	driver.serve()
	driver.logger.info("Server Process Finished")
