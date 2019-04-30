
from driver.csi.csi_pb2 import NodeGetInfoRequest, NodeGetCapabilitiesRequest, NodePublishVolumeRequest, VolumeCapability, NodeUnpublishVolumeRequest
from driver.csi.csi_pb2_grpc import NodeStub
from test.clients.base_client import BaseClient


class NodeClient(BaseClient):

	def __init__(self):
		BaseClient.__init__(self)
		self.client = NodeStub(self.intercepted_channel)

	def NodeStageVolume(self):
		raise NotImplementedError('Client Method not implemented!')

	def NodeUnstageVolume(self):
		raise NotImplementedError('Client Method not implemented!')

	def NodePublishVolume(self, volume_id):
		# message NodePublishVolumeRequest {
		#   // The ID of the volume to publish. This field is REQUIRED.
		#   string volume_id = 1;
		#
		#   // The CO SHALL set this field to the value returned by
		#   // `ControllerPublishVolume` if the corresponding Controller Plugin
		#   // has `PUBLISH_UNPUBLISH_VOLUME` controller capability, and SHALL be
		#   // left unset if the corresponding Controller Plugin does not have
		#   // this capability. This is an OPTIONAL field.
		#   map<string, string> publish_context = 2;
		#
		#   // The path to which the volume was staged by `NodeStageVolume`.
		#   // It MUST be an absolute path in the root filesystem of the process
		#   // serving this request.
		#   // It MUST be set if the Node Plugin implements the
		#   // `STAGE_UNSTAGE_VOLUME` node capability.
		#   // This is an OPTIONAL field.
		#   string staging_target_path = 3;
		#
		#   // The path to which the volume will be published. It MUST be an
		#   // absolute path in the root filesystem of the process serving this
		#   // request. The CO SHALL ensure uniqueness of target_path per volume.
		#   // The CO SHALL ensure that the parent directory of this path exists
		#   // and that the process serving the request has `read` and `write`
		#   // permissions to that parent directory.
		#   // For volumes with an access type of block, the SP SHALL place the
		#   // block device at target_path.
		#   // For volumes with an access type of mount, the SP SHALL place the
		#   // mounted directory at target_path.
		#   // Creation of target_path is the responsibility of the SP.
		#   // This is a REQUIRED field.
		#   string target_path = 4;
		target_path = '/mnt/{}'.format(volume_id)

		#   // Volume capability describing how the CO intends to use this volume.
		#   // SP MUST ensure the CO can use the published volume as described.
		#   // Otherwise SP MUST return the appropriate gRPC error code.
		#   // This is a REQUIRED field.
		#   VolumeCapability volume_capability = 5;
		volume_capability = VolumeCapability(block=VolumeCapability.BlockVolume())

		#   // Indicates SP MUST publish the volume in readonly mode.
		#   // This field is REQUIRED.
		#   bool readonly = 6;
		readonly = False

		#   // Secrets required by plugin to complete node publish volume request.
		#   // This field is OPTIONAL. Refer to the `Secrets Requirements`
		#   // section on how to use this field.
		#   map<string, string> secrets = 7 [(csi_secret) = true];
		#
		#   // Volume context as returned by CO in CreateVolumeRequest. This field
		#   // is OPTIONAL and MUST match the volume_context of the volume
		#   // identified by `volume_id`.
		#   map<string, string> volume_context = 8;
		# }

		req =  NodePublishVolumeRequest(
			volume_id=volume_id,
			target_path=target_path,
			volume_capability=volume_capability,
			readonly=readonly
		)
		return self.client.NodePublishVolume(req)

	def NodeUnpublishVolume(self, volume_id):
		target_path = '/mnt/{}'.format(volume_id)
		req = NodeUnpublishVolumeRequest(volume_id=volume_id, target_path=target_path)
		return self.client.NodeUnpublishVolume(req)

	def NodeGetVolumeStats(self):
		raise NotImplementedError('Client Method not implemented!')

	def NodeExpandVolume(self):
		raise NotImplementedError('Client Method not implemented!')

	def NodeGetCapabilities(self):
		return self.client.NodeGetCapabilities(NodeGetCapabilitiesRequest())

	def NodeGetInfo(self):
		return self.client.NodeGetInfo(NodeGetInfoRequest())
