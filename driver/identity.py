from driver.common import Consts
from driver.csi.csi_pb2 import GetPluginInfoResponse
from driver.csi.csi_pb2_grpc import IdentityServicer


class NVMeshIdentity(IdentityServicer):
	def GetPluginInfo(self, request, context):
		name = Consts.IDENTITY_NAME
		vendor_version = Consts.SERVICE_VERSION
		# OPTIONAL FIELD: map <string, string> manifest = 3;
		return GetPluginInfoResponse(name=name, vendor_version=vendor_version)

	def GetPluginCapabilities(self, request, context):
		# missing associated documentation comment in .proto file
		raise NotImplementedError('Method not implemented!')

	def Probe(self, request, context):
		# missing associated documentation comment in .proto file
		raise NotImplementedError('Method not implemented!')