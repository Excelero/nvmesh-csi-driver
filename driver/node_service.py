import json
import socket

import os

from google.protobuf.json_format import MessageToJson, MessageToDict
from grpc import StatusCode

from config import Config, get_config_json
from FileSystemManager import FileSystemManager
from common import Utils, CatchServerErrors, DriverError, FeatureSupportChecks
import consts as Consts
from csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse, \
	NodeStageVolumeResponse, NodeUnstageVolumeResponse, NodeExpandVolumeResponse, Topology
from csi.csi_pb2_grpc import NodeServicer
from topology import TopologyUtils


class NVMeshNodeService(NodeServicer):
	def __init__(self, logger):
		NodeServicer.__init__(self)
		self.node_id = socket.gethostname()

		self.logger = logger
		self.logger.info('NVMesh Version Info: {}'.format(json.dumps(Config.NVMESH_VERSION_INFO, indent=4, sort_keys=True)))

		feature_list = json.dumps(FeatureSupportChecks.get_all_features(), indent=4, sort_keys=True)
		self.logger.info('Supported Features: {}'.format(feature_list))
		self.topology = None

		self.logger.info('Config: {}'.format(get_config_json()))

	@CatchServerErrors
	def NodeStageVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'staging_target_path', 'volume_capability'])

		zone, nvmesh_volume_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)

		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		secrets = request.secrets
		publish_context = request.publish_context
		volume_context = request.volume_context

		reqJson = MessageToJson(request)
		self.logger.debug('NodeStageVolume called with request: {}'.format(reqJson))

		access_mode = volume_capability.access_mode.mode
		access_type = self._get_block_or_mount_volume(request)

		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			# run nvmesh attach locally
			requested_nvmesh_access_mode = Consts.AccessMode.to_nvmesh(access_mode)
			Utils.nvmesh_attach_volume(nvmesh_volume_name, requested_nvmesh_access_mode)

		Utils.wait_for_volume_io_enabled(nvmesh_volume_name)

		if access_type == Consts.VolumeAccessType.MOUNT:
			mount_request = volume_capability.mount
			self.logger.info('Requested Mounted FileSystem Volume with fs_type={}'.format(mount_request.fs_type))
			fs_type = mount_request.fs_type or Consts.FSType.EXT4
			mount_options = []

			if mount_request.mount_flags:
				for flag in mount_request.mount_flags:
					mount_options.append(flag)

			FileSystemManager.format_block_device(block_device_path, fs_type)

			if FileSystemManager.is_mounted(staging_target_path):
				self.logger.warning('path {} is already mounted'.format(staging_target_path))

			FileSystemManager.mount(source=block_device_path, target=staging_target_path, mount_options=mount_options)

		elif access_type == Consts.VolumeAccessType.BLOCK:
			self.logger.info('Requested Block Volume')
			# We do not mount here, NodePublishVolume will mount directly from the block device to the publish_path
			# This is because Kubernetes automatically creates a directory in the staging_path

		else:
			self.logger.Info('Unknown AccessType {}'.format(access_type))

		return NodeStageVolumeResponse()

	@CatchServerErrors
	def NodeUnstageVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'staging_target_path'])

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnstageVolume called with request: {}'.format(reqJson))

		staging_target_path = request.staging_target_path
		zone, nvmesh_volume_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)

		if os.path.exists(staging_target_path):
			FileSystemManager.umount(target=staging_target_path)

			if os.path.isfile(staging_target_path):
				self.logger.debug('NodeUnstageVolume removing stage bind file: {}'.format(staging_target_path))
				os.remove(staging_target_path)
			elif os.path.isdir(staging_target_path):
				self.logger.debug('NodeUnstageVolume removing stage dir: {}'.format(staging_target_path))
				FileSystemManager.remove_dir(staging_target_path)
		else:
			self.logger.warning('NodeUnstageVolume - mount path {} not found.'.format(staging_target_path))

		Utils.nvmesh_detach_volume(nvmesh_volume_name)

		return NodeUnstageVolumeResponse()

	@CatchServerErrors
	def NodePublishVolume(self, request, context):
		# NodePublishVolume: This method is called to mount the volume from staging to target path.
		Utils.validate_params_exists(request, ['volume_id', 'target_path'])

		zone, nvmesh_volume_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)
		staging_target_path = request.staging_target_path
		publish_path = request.target_path
		volume_capability = request.volume_capability
		access_mode = volume_capability.access_mode.mode
		readonly = request.readonly
		access_type = self._get_block_or_mount_volume(request)
		volume_context = request.volume_context
		podInfo = self._extract_pod_info_from_volume_context(volume_context)

		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)

		reqJson = MessageToJson(request)
		self.logger.debug('NodePublishVolume called with request: {}'.format(reqJson))
		self.logger.debug('NodePublishVolume podInfo: {}'.format(podInfo))

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(nvmesh_volume_name))

		mount_options = []

		if volume_capability.mount.mount_flags:
			for flag in volume_capability.mount.mount_flags:
				mount_options.append(flag)

		# K8s Bug Workaround: readonly flag is not sent to CSI, so we try to also infer from the AccessMode
		if readonly or access_mode == Consts.AccessMode.MULTI_NODE_READER_ONLY:
			mount_options.append('ro')

		if access_type == Consts.VolumeAccessType.BLOCK:
			# create an empty file for bind mount
			with open(publish_path, 'w'):
				pass

			# bind directly from block device to publish_path
			self.logger.debug('NodePublishVolume trying to bind mount as block device {} to {}'.format(block_device_path, publish_path))
			FileSystemManager.bind_mount(source=block_device_path, target=publish_path, mount_options=mount_options)
		else:
			self.logger.debug('NodePublishVolume trying to bind mount {} to {}'.format(staging_target_path, publish_path))
			FileSystemManager.bind_mount(source=staging_target_path, target=publish_path, mount_options=mount_options)

		return NodePublishVolumeResponse()

	@CatchServerErrors
	def NodeUnpublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'target_path'])

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
		nvmesh_vol_name = volume_id
		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_vol_name)

		reqJson = MessageToJson(request)
		self.logger.debug('NodeExpandVolume called with request: {}'.format(reqJson))

		fs_type = FileSystemManager.get_file_system_type(block_device_path)

		attempts_left = 20
		resized = False
		while not resized and attempts_left:
			exit_code, stdout, stderr = FileSystemManager.expand_file_system(block_device_path, fs_type)
			if 'Nothing to do!' in stderr:
				block_device_size = FileSystemManager.get_block_device_size(block_device_path)
				self.logger.warning('File System not resized. block device size is {}'.format(block_device_size))
				attempts_left = attempts_left - 1
				Utils.interruptable_sleep(2)
			else:
				resized = True

		if not attempts_left:
			raise DriverError(StatusCode.INTERNAL, 'Back-Off trying to expand {} FileSystem on volume {}'.format(fs_type, block_device_path))

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
		reqDict = MessageToDict(request)
		self.logger.debug('NodeGetInfo called with request: {}'.format(reqDict))

		if not self.topology:
			self.topology = self._get_topology()

		return NodeGetInfoResponse(node_id=self.node_id, accessible_topology=self.topology)

	def _get_block_or_mount_volume(self, request):
		volume_capability = request.volume_capability

		if volume_capability.HasField('mount'):
			return Consts.VolumeAccessType.MOUNT
		elif volume_capability.HasField('block'):
			return Consts.VolumeAccessType.BLOCK
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'at least one of volume_capability.block, volume_capability.mount must be set')

	def _extract_pod_info_from_volume_context(self, volume_context):
		if not volume_context:
			return {}

		podInfo = {
			'podName': volume_context.get('csi.storage.k8s.io/pod.name'),
			'podNamespace': volume_context.get('csi.storage.k8s.io/pod.namespace'),
			'podUid': volume_context.get('csi.storage.k8s.io/pod.uid'),
			'ephemeral': volume_context.get('csi.storage.k8s.io/ephemeral'),
			'serviceAccount': volume_context.get('csi.storage.k8s.io/serviceAccount.name')
		}

		return podInfo

	def _get_topology(self):
		self.logger.debug('_get_topology called TopologyType=%s' % Config.TOPOLOGY_TYPE)

		topology_info = {}

		if Config.TOPOLOGY_TYPE == Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS:
			zone = TopologyUtils.get_node_zone(self.node_id, logger=self.logger)
			topology_key = TopologyUtils.get_topology_key()
			topology_info[topology_key] = zone
		elif Config.TOPOLOGY_TYPE == Consts.TopologyType.SINGLE_ZONE_CLUSTER:
			topology_key = TopologyUtils.get_topology_key()
			topology_info[topology_key] = Consts.SINGLE_CLUSTER_ZONE_NAME
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Unsupported Config.TOPOLOGY_TYPE of %s' % Config.TOPOLOGY_TYPE)

		self.logger.debug('Node topology: %s' % topology_info)
		return Topology(segments=topology_info)
