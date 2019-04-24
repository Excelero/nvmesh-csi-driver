import grpc

from driver.common import Consts
from driver.csi.csi_pb2 import CreateVolumeRequest, DeleteVolumeRequest, VolumeCapability, CapacityRange
from driver.csi.csi_pb2_grpc import ControllerStub
from test.clients.base_client import BaseClient
from test.clients.client_logging_interceptor import ClientLoggingInterceptor

AccessMode = VolumeCapability.AccessMode

class ControllerClient(BaseClient):

	def __init__(self):
		BaseClient.__init__(self)
		self.channel = grpc.insecure_channel(Consts.UDS_PATH)
		self.intercepted_channel = grpc.intercept_channel(self.channel, ClientLoggingInterceptor(self.logger))
		self.client = ControllerStub(self.intercepted_channel)

	def CreateVolume(self, name, capacity_in_bytes=0):
		name = name # string

		# OPTIONAL - CapacityRange capacity_range = 2;
		capacity_range = CapacityRange(required_bytes=capacity_in_bytes)

		# REQUIRED - repeated VolumeCapability volume_capabilities = 3;
		access_mode=VolumeCapability.AccessMode(mode=AccessMode.MULTI_NODE_MULTI_WRITER)
		access_mode_capability = VolumeCapability(access_mode=access_mode)
		block_volume_capability = VolumeCapability(block=VolumeCapability.BlockVolume())
		volume_capabilities = [access_mode_capability, block_volume_capability]
		# OPTIONAL - map < string, string > parameters = 4;
		# OPTIONAL - map < string, string > secrets = 5[(csi_secret) = true];
		# OPTIONAL - VolumeContentSource volume_content_source = 6;
		# OPTIONAL - TopologyRequirement accessibility_requirements = 7;

		req = CreateVolumeRequest(
			name=name,
			capacity_range=capacity_range,
			volume_capabilities=volume_capabilities
		)

		return self.client.CreateVolume(req)

	def DeleteVolume(self, volume_id):
		return self.client.DeleteVolume(DeleteVolumeRequest(volume_id=volume_id))

	def close(self):
		self.channel.close()

	def __del__(self):
		self.close()