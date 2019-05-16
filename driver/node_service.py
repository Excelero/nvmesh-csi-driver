import socket

import os

from google.protobuf.json_format import MessageToJson
from grpc import StatusCode

from driver.FileSystemManager import FileSystemManager
from driver.common import Utils, CatchServerErrors, DriverError, Consts
from driver.csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse, \
	NodeStageVolumeResponse, NodeUnstageVolumeResponse, VolumeCapability, NodeExpandVolumeResponse
from driver.csi.csi_pb2_grpc import NodeServicer


class NVMeshNodeService(NodeServicer):
	def __init__(self, logger):
		NodeServicer.__init__(self)
		self.logger = logger

	@CatchServerErrors
	def NodeStageVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'staging_target_path', 'volume_capability'])

		volume_id = request.volume_id
		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		secrets = request.secrets
		publish_context = request.publish_context
		volume_context = request.volume_context

		reqJson = MessageToJson(request)
		self.logger.debug('NodeStageVolume called with request: {}'.format(reqJson))

		access_mode = volume_capability.access_mode.mode
		access_type = self._get_block_or_mount_volume(request)

		nvmesh_volume_name = Utils.volume_id_to_nvmesh_name(volume_id)
		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(nvmesh_volume_name))

		if access_type == Consts.VolumeAccessType.MOUNT:
			mount_request = volume_capability.mount
			self.logger.info('Requested Mounted FileSystem Volume with fs_type={}'.format(mount_request.fs_type))
			fs_type = mount_request.fs_type or 'ext4'
			mount_flags = mount_request.mount_flags

			FileSystemManager.format_block_device(block_device_path, fs_type)

			if FileSystemManager.is_mounted(staging_target_path):
				self.logger.warning('path {} is already mounted'.format(staging_target_path))

			FileSystemManager.mount(source=block_device_path, target=staging_target_path, flags=mount_flags)

		elif access_type == Consts.VolumeAccessType.BLOCK:
			self.logger.info('Requested Block Volume')
			if access_mode != VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER:
				requested_access_mode_name = VolumeCapability.AccessMode.Mode._enum_type.values_by_number[access_mode].name
				raise DriverError(StatusCode.INVALID_ARGUMENT, 'accessMode {} not supported. Only MULTI_NODE_MULTI_WRITER is supported with block volume'.format(requested_access_mode_name))

			try:
				if os.path.isfile(staging_target_path):
					self.logger.debug('staging_target_path {} is a file'.format(staging_target_path))
				elif os.path.isdir(staging_target_path):
					self.logger.debug('staging_target_path {} is a dir. removing the dir and creating a file instead'.format(staging_target_path))
					FileSystemManager.remove_dir(staging_target_path)
					# create an empty file for bind mount
					open(staging_target_path, 'w').close()
				else:
					self.logger.debug('staging_target_path {} is NOT a file or a dir'.format(staging_target_path))
					open(staging_target_path, 'w').close()

				self.logger.debug('Trying to bind mount Block volume {} to {}'.format(block_device_path, staging_target_path))
				FileSystemManager.bind_mount(source=block_device_path, target=staging_target_path)
			except Exception as ex:
				errMessage = 'Error Failed to bind mount Block volume {} to {}. Error: {}'.format(block_device_path, staging_target_path, str(ex))
				raise DriverError(StatusCode.INTERNAL, errMessage)

		else:
			self.logger.Info('Unknown AccessType {}'.format(access_type))

		return NodeStageVolumeResponse()

	@CatchServerErrors
	def NodeUnstageVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'staging_target_path'])

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnstageVolume called with request: {}'.format(reqJson))

		staging_target_path = request.staging_target_path

		if not os.path.exists(staging_target_path):
			raise DriverError(StatusCode.NOT_FOUND, 'mount path {} not found'.format(staging_target_path))
		else:
			FileSystemManager.umount(target=staging_target_path)

		if os.path.isfile(staging_target_path):
			self.logger.debug('NodeUnstageVolume removing stage bind file: {}'.format(staging_target_path))
			os.remove(staging_target_path)
		elif os.path.isdir(staging_target_path):
			self.logger.debug('NodeUnstageVolume removing stage dir: {}'.format(staging_target_path))
			FileSystemManager.remove_dir(staging_target_path)

		return NodeUnstageVolumeResponse()

	@CatchServerErrors
	def NodePublishVolume(self, request, context):
		# NodePublishVolume: This method is called to mount the volume from staging to target path.
		Utils.validate_params_exists(request, ['volume_id', 'target_path'])

		volume_id = request.volume_id
		nvmesh_volume_name = Utils.volume_id_to_nvmesh_name(volume_id)
		staging_target_path = request.staging_target_path
		publish_path = request.target_path
		volume_capability = request.volume_capability
		readonly = request.readonly
		access_type = self._get_block_or_mount_volume(request)

		reqJson = MessageToJson(request)
		self.logger.debug('NodePublishVolume called with request: {}'.format(reqJson))

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(nvmesh_volume_name))

		flags = []
		if readonly:
			flags.append('-o ro')

		if access_type == Consts.VolumeAccessType.BLOCK:
			# create an empty file for bind mount
			with open(publish_path, 'w+'):
				pass

		self.logger.debug('NodePublishVolume trying to bind mount {} to {}'.format(staging_target_path, publish_path))
		FileSystemManager.bind_mount(source=staging_target_path, target=publish_path, flags=flags)

		return NodePublishVolumeResponse()

	@CatchServerErrors
	def NodeUnpublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'target_path'])

		volume_id = request.volume_id
		target_path = request.target_path

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnpublishVolume called with request: {}'.format(reqJson))

		if not os.path.exists(target_path):
			raise DriverError(StatusCode.NOT_FOUND, 'mount path {} not found'.format(target_path))

		if not FileSystemManager.is_mounted(mount_path=target_path):
			self.logger.debug('NodeUnpublishVolume: {} is already not mounted'.format(target_path))
		else:
			FileSystemManager.umount(target=target_path)

		block_device_publish_path = target_path + '/mount'
		if os.path.isfile(block_device_publish_path):
			self.logger.debug('NodeUnpublishVolume removing publish bind file: {}'.format(block_device_publish_path))
			os.remove(block_device_publish_path)
			if os.path.isfile(block_device_publish_path):
				raise DriverError(StatusCode.INTERNAL, 'node-driver unable to delete publish path')

		if os.path.isdir(target_path):
			self.logger.debug('NodeUnpublishVolume removing publish dir: {}'.format(target_path))
			FileSystemManager.remove_dir(target_path)
			if os.path.isdir(target_path):
				raise DriverError(StatusCode.INTERNAL, 'node-driver unable to delete publish directory')

		return NodeUnpublishVolumeResponse()

	@CatchServerErrors
	def NodeGetVolumeStats(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def NodeExpandVolume(self, request, context):
		# if this function was called, assume the Controller checked that this volume is a FileSystem Mounted Volume.
		# So we will resize the File System here
		volume_id = request.volume_id
		volume_path = request.volume_path
		capacity_range = request.capacity_range
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(volume_id)
		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_vol_name)

		reqJson = MessageToJson(request)
		self.logger.debug('NodeExpandVolume called with request: {}'.format(reqJson))

		fs_type = FileSystemManager.get_file_system_type(block_device_path)
		FileSystemManager.expand_file_system(block_device_path, fs_type)

		self.logger.debug('Finished Expanding File System of type {} on volume {}'.format(fs_type, block_device_path))
		return NodeExpandVolumeResponse()

	@CatchServerErrors
	def NodeGetCapabilities(self, request, context):
		# NodeServiceCapability types UNKNOWN, STAGE_UNSTAGE_VOLUME, GET_VOLUME_STATS, EXPAND_VOLUME

		def buildCapability(type):
			return NodeServiceCapability(rpc=NodeServiceCapability.RPC(type=type))

		#get_volume_stats = buildCapability(NodeServiceCapability.RPC.GET_VOLUME_STATS)
		stage_unstage = buildCapability(NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME)
		expand_volume = buildCapability(NodeServiceCapability.RPC.EXPAND_VOLUME)

		capabilities = [stage_unstage, expand_volume]

		return NodeGetCapabilitiesResponse(capabilities=capabilities)

	@CatchServerErrors
	def NodeGetInfo(self, request, context):
		return NodeGetInfoResponse(node_id=socket.gethostname())

	def _get_block_or_mount_volume(self, request):
		volume_capability = request.volume_capability

		if volume_capability.HasField('mount'):
			return Consts.VolumeAccessType.MOUNT
		elif volume_capability.HasField('block'):
			return Consts.VolumeAccessType.BLOCK
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'at least one of volume_capability.block, volume_capability.mount must be set')


