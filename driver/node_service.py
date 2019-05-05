import socket

import os

import shutil
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
		block_device_path = '/dev/nvmesh/{}'.format(nvmesh_volume_name)

		# TODO: For Debugging Purposes Only !
		# The next lines should be removed after testing on an actual kubernetes cluster
		# if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
		# 	FileSystemManager.create_fake_nvmesh_block_device(block_device_path)
		# END OF FAKE DEVICE

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(nvmesh_volume_name))

		if mount_request and mount_request.fs_type:
			self.logger.debug('requested mounted FileSystem Volume with fs_type={}'.format(mount_request.fs_type))
			fs_type = mount_request.fs_type or 'ext4'
			mount_flags = mount_request.mount_flags

			# check if already formatted, and if format meets request
			current_fs_type = FileSystemManager.get_fs_type(block_device_path)
			self.logger.debug('current_fs_type={}'.format(current_fs_type))

			if current_fs_type == fs_type:
				self.logger.debug('{} is already formatted to {}'.format(block_device_path, current_fs_type))
			else:
				if current_fs_type != '':
					self.logger.debug('{} is formatted to {} but requested {}'.format(block_device_path, current_fs_type, fs_type))
					# TODO: should we throw an error ?
				else:
					FileSystemManager.mkfs(fs_type=fs_type, target_path=block_device_path, flags=['-F'])

			if FileSystemManager.is_mounted(staging_target_path):
				self.logger.debug('path {} is already mounted'.format(staging_target_path))

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

		if os.path.isdir(staging_target_path):
			self.logger.debug('NodeUnstageVolume removing stage dir: {}'.format(staging_target_path))
			FileSystemManager.remove_dir(staging_target_path)

		# TODO: For Debugging Purposes Only !
		# nvmesh_volume_name = Utils.volume_id_to_nvmesh_name(request.volume_id)
		# block_device_path = '/dev/nvmesh/{}'.format(nvmesh_volume_name)
		# if os.path.isfile(block_device_path):
		# 	os.remove(block_device_path)

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

		if not Utils.is_nvmesh_volume_attached(volume_id):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(volume_id))
		if not FileSystemManager.is_mounted(staging_target_path):
			raise DriverError(StatusCode.FAILED_PRECONDITION, 'staging_target_path {} was not found'.format(staging_target_path))

		FileSystemManager.bind_mount(source=staging_target_path, target=target_path)
		return NodePublishVolumeResponse()

	def NodeUnpublishVolume(self, request, context):
		volume_id = request.volume_id
		target_path = request.target_path

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnpublishVolume called with request: {}'.format(reqJson))

		self.logger.debug("NodeUnpublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		if FileSystemManager.is_mounted(mount_path=target_path):
			self.logger.debug("NodeUnpublishVolume: {} is already not mounted".format(target_path))

		FileSystemManager.umount(target=target_path)

		if os.path.isdir(target_path):
			self.logger.debug('NodeUnpublishVolume removing publish dir: {}'.format(target_path))
			FileSystemManager.remove_dir(target_path)
			if os.path.isdir(target_path):
				raise DriverError(StatusCode.INTERNAL, 'node-driver unable to delete publish directory')

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

