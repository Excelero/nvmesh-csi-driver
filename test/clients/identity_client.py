import grpc
from driver.common import Consts
from driver.csi.csi_pb2 import GetPluginInfoRequest, GetPluginCapabilitiesRequest, ProbeRequest
from driver.csi.csi_pb2_grpc import IdentityStub
from test.clients.base_client import BaseClient
from test.clients.client_logging_interceptor import ClientLoggingInterceptor


class IdentityClient(BaseClient):

	def __init__(self):
		BaseClient.__init__(self)
		self.channel = grpc.insecure_channel(Consts.UDS_PATH)
		self.intercepted_channel = grpc.intercept_channel(self.channel, ClientLoggingInterceptor(self.logger))
		self.client = IdentityStub(self.intercepted_channel)

	def GetPluginInfo(self):
		return self.client.GetPluginInfo(GetPluginInfoRequest())

	def GetPluginCapabilities(self):
		return self.client.GetPluginCapabilities(GetPluginCapabilitiesRequest())

	def Probe(self):
		return self.client.Probe(ProbeRequest())

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()

