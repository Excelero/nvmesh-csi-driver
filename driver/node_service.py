import socket
from google.protobuf.json_format import MessageToJson
from grpc import StatusCode

from driver.FileSystemManager import FileSystemManager
from driver.common import Utils, CatchServerErrors, DriverError
from driver.csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse, \
	NodeStageVolumeResponse, NodeUnstageVolumeResponse, VolumeCapability
from driver.csi.csi_pb2_grpc import NodeServicer


class NVMeshNodeService(NodeServicer):
	def __init__(self, logger):
		NodeServicer.__init__(self)
		self.logger = logger

	@CatchServerErrors
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

		reqJson = MessageToJson(request)
		self.logger.debug('NodeStageVolume called with request: {}'.format(reqJson))

		access_mode = volume_capability.access_mode.mode
		block_volume = volume_capability.block
		mount_request = volume_capability.mount

		nvmesh_volume_name = Utils.volume_id_to_nvmesh_name(volume_id)

		block_device_path = FileSystemManager.create_fake_nvmesh_block_device(nvmesh_volume_name)

		if mount_request and mount_request.fs_type:
			self.logger.debug("requested mounted FileSystem Volume with fs_type = {}".format(mount_request.fs_type))
			fs_type = mount_request.fs_type or "ext4"
			mount_flags = mount_request.mount_flags

			# TODO: check if already formatted, and if format meets request
			FileSystemManager.mkfs(fs_type=fs_type, target_path=block_device_path, flags=['-F'])
			FileSystemManager.mount(source=block_device_path, target=staging_target_path, flags=mount_flags)

		elif block_volume:
			self.logger.debug("requested Block Volume")
			if access_mode != VolumeCapability.AccesMode.MULTI_NODE_MULTI_WRITER:
				requested_access_mode_name = VolumeCapability.AccessMode.Mode._enum_type.values_by_number[access_mode].name
				raise DriverError(StatusCode.INVALID_ARGUMENT, "accessMode {} not supported. Only MULTI_NODE_MULTI_WRITER is supported".format(requested_access_mode_name))

			FileSystemManager.bind_mount(source=block_device_path, target=staging_target_path)

		return NodeStageVolumeResponse()

	def NodeUnstageVolume(self, request, context):
		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnstageVolume called with request: {}'.format(reqJson))

		staging_target_path = request.staging_target_path
		FileSystemManager.umount(target=staging_target_path)
		return NodeUnstageVolumeResponse()

	def NodePublishVolume(self, request, context):
		# NodePublishVolume: This method is called to mount the volume from staging to target path.
		# Usually what you do here is a bind mount. A bind mount allows you to mount a path to a different path (instead of mounting a device to a path).
		# In Kubernetes, this allows us for example to use the mounted volume from the staging path
		# (i.e global directory) to the target path (pod directory).
		# Here, formatting is not needed because we already did it in NodeStageVolume.

		volume_id = request.volume_id
		staging_target_path = request.staging_target_path
		target_path = request.target_path
		volume_capability = request.volume_capability
		readonly = request.readonly

		self.logger.debug("NodePublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))

		reqJson = MessageToJson(request)
		self.logger.debug('NodePublishVolume called with request: {}'.format(reqJson))

		FileSystemManager.bind_mount(source=staging_target_path, target=target_path)
		return NodePublishVolumeResponse()

	def NodeUnpublishVolume(self, request, context):
		volume_id = request.volume_id
		target_path = request.target_path

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnpublishVolume called with request: {}'.format(reqJson))

		self.logger.debug("NodeUnpublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		FileSystemManager.umount(target=target_path)

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
		stage_unstage = buildCapability(NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME)

		capabilities = [stage_unstage]

		return NodeGetCapabilitiesResponse(capabilities=capabilities)

	def NodeGetInfo(self, request, context):
		return NodeGetInfoResponse(node_id=socket.gethostname())

