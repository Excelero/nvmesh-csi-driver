import grpc

from driver.common import Consts
from driver.csi.csi_pb2 import CreateVolumeRequest, DeleteVolumeRequest, VolumeCapability, CapacityRange, ControllerPublishVolumeRequest, \
	ControllerUnpublishVolumeRequest, ValidateVolumeCapabilitiesRequest, ListVolumesRequest, ControllerGetCapabilitiesRequest, ControllerExpandVolumeRequest
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

	def _getDefaultVolumeCapabilities(self):
		access_mode = VolumeCapability.AccessMode(mode=AccessMode.MULTI_NODE_MULTI_WRITER)
		access_mode_capability = VolumeCapability(access_mode=access_mode)
		block_volume_capability = VolumeCapability(block=VolumeCapability.BlockVolume())
		volume_capabilities = [access_mode_capability, block_volume_capability]
		return volume_capabilities


	def CreateVolume(self, name, capacity_in_bytes=0):
		name = name # string

		# OPTIONAL - CapacityRange capacity_range = 2;
		capacity_range = CapacityRange(required_bytes=capacity_in_bytes)

		# REQUIRED - repeated VolumeCapability volume_capabilities = 3;
		volume_capabilities = self._getDefaultVolumeCapabilities()
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

	def PublishVolume(self, volume_id, node_id):
		# // The ID of the volume to be used on a node.
		# // This field is REQUIRED.
		# string volume_id = 1;
		#
		# // The ID of the node. This field is REQUIRED. The CO SHALL set this
		# // field to match the node ID returned by `NodeGetInfo`.
		# string node_id = 2;
		#
		# // Volume capability describing how the CO intends to use this volume.
		# // SP MUST ensure the CO can use the published volume as described.
		# // Otherwise SP MUST return the appropriate gRPC error code.
		# // This is a REQUIRED field.
		# VolumeCapability volume_capability = 3;

		volume_capability = VolumeCapability()
		# // Indicates SP MUST publish the volume in readonly mode.
		# // CO MUST set this field to false if SP does not have the
		# // PUBLISH_READONLY controller capability.
		# // This is a REQUIRED field.
		# bool readonly = 4;

		readonly=False
		# // Secrets required by plugin to complete controller publish volume
		# // request. This field is OPTIONAL. Refer to the
		# // `Secrets Requirements` section on how to use this field.
		# map<string, string> secrets = 5 [(csi_secret) = true];
		#
		# // Volume context as returned by CO in CreateVolumeRequest. This field
		# // is OPTIONAL and MUST match the volume_context of the volume
		# // identified by `volume_id`.
		# map<string, string> volume_context = 6;


		req = ControllerPublishVolumeRequest(
			volume_id=volume_id,
			node_id=node_id,
			volume_capability=volume_capability,
			readonly=readonly)

		return self.client.ControllerPublishVolume(req)

	def UnpublishVolume(self, volume_id, node_id):
		req = ControllerUnpublishVolumeRequest(volume_id=volume_id, node_id=node_id)
		return self.client.ControllerUnpublishVolume(req)

	def ValidateVolumeCapabilities(self, volume_id):
		# // The ID of the volume to check. This field is REQUIRED.
		# string volume_id = 1;

		# // Volume context as returned by CO in CreateVolumeRequest. This field
		# // is OPTIONAL and MUST match the volume_context of the volume
		# // identified by `volume_id`.
		# map<string, string> volume_context = 2;
		#
		# // The capabilities that the CO wants to check for the volume. This
		# // call SHALL return "confirmed" only if all the volume capabilities
		# // specified below are supported. This field is REQUIRED.
		# repeated VolumeCapability volume_capabilities = 3;
		volume_capabilities = self._getDefaultVolumeCapabilities()

		# // See CreateVolumeRequest.parameters.
		# // This field is OPTIONAL.
		# map<string, string> parameters = 4;
		#
		# // Secrets required by plugin to complete volume validation request.
		# // This field is OPTIONAL. Refer to the `Secrets Requirements`
		# // section on how to use this field.
		# map<string, string> secrets = 5 [(csi_secret) = true];
		req = ValidateVolumeCapabilitiesRequest(volume_id=volume_id, volume_capabilities=volume_capabilities)
		return self.client.ValidateVolumeCapabilities(req)

	def ListVolumes(self, max_entries, starting_token=""):
		req = ListVolumesRequest(max_entries=max_entries, starting_token=starting_token)
		return self.client.ListVolumes(req)

	def GetCapabilities(self):
		req = ControllerGetCapabilitiesRequest()
		return self.client.ControllerGetCapabilities(req)

	def ControllerExpandVolume(self, volume_id, new_capacity_in_bytes):

		# message ControllerExpandVolumeRequest {
		#   // The ID of the volume to expand. This field is REQUIRED.
		#   string volume_id = 1;
		#
		#   // This allows CO to specify the capacity requirements of the volume
		#   // after expansion. This field is REQUIRED.
		#   CapacityRange capacity_range = 2;

		capacity_range = CapacityRange(required_bytes=new_capacity_in_bytes)
		#   // Secrets required by the plugin for expanding the volume.
		#   // This field is OPTIONAL.
		#   map<string, string> secrets = 3 [(csi_secret) = true];
		# }

		req = ControllerExpandVolumeRequest(volume_id=volume_id, capacity_range=capacity_range)
		return self.client.ControllerExpandVolume(req)