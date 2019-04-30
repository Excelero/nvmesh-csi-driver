import google as google

from driver.common import Consts
from driver.csi.csi_pb2 import GetPluginInfoResponse, ProbeResponse, GetPluginCapabilitiesResponse, PluginCapability
from driver.csi.csi_pb2_grpc import IdentityServicer


class NVMeshIdentityService(IdentityServicer):
	def __init__(self, logger):
		IdentityServicer.__init__(self)
		self.logger = logger

	def GetPluginInfo(self, request, context):
		name = Consts.PLUGIN_NAME
		vendor_version = Consts.PLUGIN_VERSION
		# OPTIONAL FIELD: map <string, string> manifest = 3;
		return GetPluginInfoResponse(name=name, vendor_version=vendor_version)

	def GetPluginCapabilities(self, request, context):
		ctrl_service = PluginCapability.Service(type=PluginCapability.Service.CONTROLLER_SERVICE)
		plugin_capability = PluginCapability(service=ctrl_service)

		capabilities = [
			plugin_capability
		]

		return GetPluginCapabilitiesResponse(capabilities=capabilities)

	def Probe(self, request, context):
		ready = google.protobuf.wrappers_pb2.BoolValue(value=True)
		return ProbeResponse(ready=ready)