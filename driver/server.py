import grpc
import time
from concurrent import futures

from driver.common import Consts, ServerLoggingInterceptor, DriverLogger
from driver.controller_service import NVMeshControllerService
from driver.csi import csi_pb2_grpc
from driver.identity_service import NVMeshIdentityService
from driver.node_service import NVMeshNodeService

_ONE_DAY_IN_SECONDS = 60 * 60 * 24

class NVMeshCSIDriverServer(object):

	def __init__(self, logger):
		self.identity_service = NVMeshIdentityService()
		self.controller_service = NVMeshControllerService()
		self.node_service = NVMeshNodeService()
		self.logger = logger

	def serve(self):
		logging_interceptor = ServerLoggingInterceptor(self.logger)
		server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),interceptors=(logging_interceptor,))
		csi_pb2_grpc.add_IdentityServicer_to_server(self.identity_service, server)
		csi_pb2_grpc.add_ControllerServicer_to_server(self.controller_service, server)
		csi_pb2_grpc.add_NodeServicer_to_server(self.node_service, server)
		server.add_insecure_port(Consts.UDS_PATH)
		server.start()
		try:
			while True:
				time.sleep(_ONE_DAY_IN_SECONDS)
		except KeyboardInterrupt:
			server.stop(0)

if __name__ == '__main__':
	logger = DriverLogger()
	driver = NVMeshCSIDriverServer(logger)
	driver.serve()
