import socket

from driver.csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse, \
	NodeStageVolumeResponse, NodeUnstageVolumeResponse
from driver.csi.csi_pb2_grpc import NodeServicer
from managementClient.ManagementClientWrapper import ManagementClientWrapper


class NVMeshNodeService(NodeServicer):
	def __init__(self):
		NodeServicer.__init__(self)
		self.mgmtClient = ManagementClientWrapper()

	def NodeStageVolume(self, request, context):
		# NodeStageVolume: This method is called by the CO to temporarily mount the volume to a staging path.
		# Usually this staging path is a global directory on the node.
		# In Kubernetes, after it's mounted to the global directory, you mount it into the pod directory (via NodePublishVolume).
		# The reason that mounting is a two step operation is because Kubernetes allows you to use a single volume by multiple pods.
		# This is allowed when the storage system supports it (say NFS) or if all pods run on the same node.
		# One thing to note is that you also need to format the volume if it's not formatted already. Keep that in mind.

			# // The ID of the volume to publish. This field is REQUIRED.
			# string volume_id = 1;

			# // The CO SHALL set this field to the value returned by
			# // `ControllerPublishVolume` if the corresponding Controller Plugin
			# // has `PUBLISH_UNPUBLISH_VOLUME` controller capability, and SHALL be
			# // left unset if the corresponding Controller Plugin does not have
			# // this capability. This is an OPTIONAL field.
			# map<string, string> publish_context = 2;

			# // The path to which the volume MAY be staged. It MUST be an
			# // absolute path in the root filesystem of the process serving this
			# // request, and MUST be a directory. The CO SHALL ensure that there
			# // is only one `staging_target_path` per volume. The CO SHALL ensure
			# // that the path is directory and that the process serving the
			# // request has `read` and `write` permission to that directory. The
			# // CO SHALL be responsible for creating the directory if it does not
			# // exist.
			# // This is a REQUIRED field.
			# string staging_target_path = 3;
			#
			# // Volume capability describing how the CO intends to use this volume.
			# // SP MUST ensure the CO can use the staged volume as described.
			# // Otherwise SP MUST return the appropriate gRPC error code.
			# // This is a REQUIRED field.
			# VolumeCapability volume_capability = 4;
			#
			# // Secrets required by plugin to complete node stage volume request.
			# // This field is OPTIONAL. Refer to the `Secrets Requirements`
			# // section on how to use this field.
			# map<string, string> secrets = 5 [(csi_secret) = true];
			#
			# // Volume context as returned by CO in CreateVolumeRequest. This field
			# // is OPTIONAL and MUST match the volume_context of the volume
			# // identified by `volume_id`.
			# map<string, string> volume_context = 6;
		volume_id = request.volume_id
		publish_context = request.publish_context
		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		secrets = request.secrets
		volume_context = request.volume_context

		# TODO: should we mount to a global path ?
		raise NotImplementedError('Method not implemented!')
		return NodeStageVolumeResponse()

	def NodeUnstageVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')
		return NodeUnstageVolumeResponse()

	def NodePublishVolume(self, request, context):
		# NodePublishVolume: This method is called to mount the volume from staging to target path.
		# Usually what you do here is a bind mount. A bind mount allows you to mount a path to a different path (instead of mounting a device to a path).
		# In Kubernetes, this allows us for example to use the mounted volume from the staging path
		# (i.e global directory) to the target path (pod directory).
		# Here, formatting is not needed because we already did it in NodeStageVolume.

		volume_id = request.volume_id
		target_path = request.target_path
		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		readonly = request.readonly

		print("NodePublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		# TODO: what should we do here ?
		# should we set the attach path ? (can we ?)
		# should we mount the volume onto the filesystem ?

		return NodePublishVolumeResponse()

	def NodeUnpublishVolume(self, request, context):
		volume_id = request.volume_id
		target_path = request.target_path

		print("NodeUnpublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		# TODO: what should we do here ?
		return NodeUnpublishVolumeResponse()

	def NodeGetVolumeStats(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeExpandVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeGetCapabilities(self, request, context):
		# NodeServiceCapability types
		# enum Type {
		# 		UNKNOWN = 0;
		# 		STAGE_UNSTAGE_VOLUME = 1;
		# 		// If Plugin implements GET_VOLUME_STATS capability
		# 		// then it MUST implement NodeGetVolumeStats RPC
		# 		// call for fetching volume statistics.
		# 		GET_VOLUME_STATS = 2;
		# 		// See VolumeExpansion for details.
		# 		EXPAND_VOLUME = 3;
		#	}
		def buildCapability(type):
			return NodeServiceCapability(rpc=NodeServiceCapability.RPC(type=type))

		get_volume_stats = buildCapability(NodeServiceCapability.RPC.GET_VOLUME_STATS)

		capabilities = []

		return NodeGetCapabilitiesResponse(capabilities=capabilities)

	def NodeGetInfo(self, request, context):
		return NodeGetInfoResponse(node_id=socket.gethostname())

