import grpc
from driver.common import Consts
from driver.csi.csi_pb2 import GetPluginInfoRequest
from driver.csi.csi_pb2_grpc import IdentityStub

class IdentityClient(object):

	def __init__(self):
		self.channel = grpc.insecure_channel(Consts.UDS_PATH)
		self.client = IdentityStub(self.channel)

	def GetPluginInfo(self):
		return self.client.GetPluginInfo(GetPluginInfoRequest())

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()
