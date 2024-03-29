from driver.csi.csi_pb2 import GetPluginInfoRequest, GetPluginCapabilitiesRequest, ProbeRequest
from driver.csi.csi_pb2_grpc import IdentityStub
from test.sanity.clients.base_client import BaseClient


class IdentityClient(BaseClient):

	def __init__(self, **kwargs):
		BaseClient.__init__(self, **kwargs)
		self.client = IdentityStub(self.intercepted_channel)

	def GetPluginInfo(self):
		return self.client.GetPluginInfo(GetPluginInfoRequest())

	def GetPluginCapabilities(self):
		return self.client.GetPluginCapabilities(GetPluginCapabilitiesRequest())

	def Probe(self):
		return self.client.Probe(ProbeRequest())
