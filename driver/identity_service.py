import google as google

from config import Config, config_loader
from csi.csi_pb2 import GetPluginInfoResponse, ProbeResponse, GetPluginCapabilitiesResponse, PluginCapability
from csi.csi_pb2_grpc import IdentityServicer


class NVMeshIdentityService(IdentityServicer):
	def __init__(self, logger):
		config_loader.load()
		IdentityServicer.__init__(self)
		self.logger = logger

	def GetPluginInfo(self, request, context):
		name = Config.DRIVER_NAME
		vendor_version = Config.DRIVER_VERSION
		# OPTIONAL FIELD: map <string, string> manifest = 3;
		return GetPluginInfoResponse(name=name, vendor_version=vendor_version)

	def GetPluginCapabilities(self, request, context):
		ctrl_service = PluginCapability(service=PluginCapability.Service(type=PluginCapability.Service.CONTROLLER_SERVICE))
		volume_expansion = PluginCapability(volume_expansion=PluginCapability.VolumeExpansion(type=PluginCapability.VolumeExpansion.ONLINE))
		capabilities = [
			ctrl_service,
			volume_expansion
		]

		return GetPluginCapabilitiesResponse(capabilities=capabilities)

	def Probe(self, request, context):
		ready = google.protobuf.wrappers_pb2.BoolValue(value=True)
		return ProbeResponse(ready=ready)
