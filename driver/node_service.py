import json
import socket

import os

from google.protobuf.json_format import MessageToJson, MessageToDict
from grpc import StatusCode

from config import Config, get_config_json
from filesystem_manager import FileSystemManager
from common import Utils, CatchServerErrors, DriverError, BackoffDelayWithStopEvent
import consts as Consts
from csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse, \
	NodeStageVolumeResponse, NodeUnstageVolumeResponse, NodeExpandVolumeResponse, Topology
from csi.csi_pb2_grpc import NodeServicer
from attach_detach_addon_to_sdk import NewClientAPI
from topology_utils import TopologyUtils, NodeNotFoundInTopology
from version_compatibility import CompatibilityValidator, VersionMatrix, VersionFetcher
from dmcrypt import DMCrypt
from consts import FSType


class NVMeshNodeService(NodeServicer):
	def __init__(self, logger, stop_event):
		NodeServicer.__init__(self)
		self.node_id = socket.gethostname()
		self.zone = None

		self.logger = logger
		self.stop_event = stop_event

		self.logger.info('Node ID: {}'.format(self.node_id))
		self.logger.info('NVMesh Version Info: {}'.format(json.dumps(Config.NVMESH_VERSION_INFO, indent=4, sort_keys=True)))
		self.logger.info('Config: {}'.format(get_config_json()))

		self.topology = None

	def init(self):
		self.topology = self._get_topology()
		self.validate_versions()

	def validate_versions(self):
		ver_mat = VersionMatrix()
		ver_mat.load_from_config_map()
		validator = CompatibilityValidator(ver_mat)

		nvmesh_core_version = VersionFetcher.get_nvmesh_core_version()
		validator.validate_nvmesh_core(nvmesh_core_version)

	@CatchServerErrors
	def NodeStageVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'staging_target_path', 'volume_capability'])

		zone, nvmesh_volume_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)

		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		secrets = request.secrets
		publish_context = request.publish_context
		volume_context = request.volume_context

		req_json = MessageToJson(request)

		# Make sure not to print secret values in log
		req_json = Utils.hide_secrets_from_message(req_json)
		self.logger.debug('NodeStageVolume called with request: {}'.format(req_json))

		access_mode = volume_capability.access_mode.mode
		access_type = self._get_block_or_mount_volume(request)

		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)
		client_api = self.get_client_api()
		encryption = volume_context.get('encryption')

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			# run nvmesh attach locally
			requested_nvmesh_access_mode = Consts.AccessMode.to_nvmesh(access_mode)
			Utils.nvmesh_attach_volume(self.node_id, client_api, nvmesh_volume_name, requested_nvmesh_access_mode)

		try:
			Utils.wait_for_volume_io_enabled(nvmesh_volume_name)

			# mapped_device is /dev/nvmesh/{vol} unless we use encryption then it is /dev/mapper/{vol}
			mapped_device = block_device_path
			
			# check if encryption required
			if encryption:
				if encryption != 'dmcrypt':
					raise DriverError(StatusCode.INVALID_ARGUMENT, "Unknown encryption type %s" % encryption)

				dmCryptKey = secrets.get('dmcryptKey')

				self.open_or_create_dmcrypt_device(nvmesh_volume_name, dmCryptKey, volume_context)
				mapped_device = DMCrypt.get_mapped_device_path(nvmesh_volume_name)

			if access_type == Consts.VolumeAccessType.MOUNT:
				mount_request = volume_capability.mount
				self.logger.info('Requested Mounted FileSystem Volume with fs_type={}'.format(mount_request.fs_type))
				fs_type = mount_request.fs_type or Consts.FSType.EXT4

				mount_permissions, mount_options = self._parse_mount_options(mount_request)
				mkfs_options = volume_context.get('mkfsOptions', '')
				FileSystemManager.format_block_device(mapped_device, fs_type, mkfs_options)

				if FileSystemManager.is_mounted(staging_target_path):
					self.logger.warning('path {} is already mounted'.format(staging_target_path))

				FileSystemManager.mount(source=mapped_device, target=staging_target_path, mount_options=mount_options)
				FileSystemManager.chmod(mount_permissions or Consts.DEFAULT_MOUNT_PERMISSIONS, staging_target_path)
			elif access_type == Consts.VolumeAccessType.BLOCK:
				self.logger.info('Requested Block Volume')
				# We do not mount here, NodePublishVolume will mount directly from the block device to the publish_path
				# This is because Kubernetes automatically creates a directory in the staging_path

			else:
				self.logger.info('Unknown AccessType {}'.format(access_type))
		except Exception as staging_err:
			# Cleanup - un-mount and detach the volume
			self.logger.warning('Failed to stage volume. Error: %s' % staging_err)
			try:
				if FileSystemManager.is_mounted(staging_target_path):
					FileSystemManager.umount(staging_target_path)

				if encryption and DMCrypt.is_open(nvmesh_volume_name):
					# dmcrypt cleanup
					self.close_dmcrypt_device(nvmesh_volume_name)

				Utils.nvmesh_detach_volume(self.node_id, client_api, nvmesh_volume_name, force=True, stop_event=self.stop_event)
			except Exception as cleanup_err:
				self.logger.warning('Failed to cleanup and detach device after attached and staging failed. Error: %s' % cleanup_err)
				raise cleanup_err
			# Re-raise the initial exception
			raise staging_err

		self.logger.debug('NodeStageVolume finished successfully for request: {}'.format(req_json))
		return NodeStageVolumeResponse()

	def get_client_api(self):
		api_params = TopologyUtils.get_api_params(self.zone)
		client_api = NewClientAPI(**api_params)
		return client_api

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

		if DMCrypt.is_open(nvmesh_volume_name):
			self.close_dmcrypt_device(nvmesh_volume_name)

		client_api = self.get_client_api()
		Utils.nvmesh_detach_volume(self.node_id, client_api, nvmesh_volume_name, Config.FORCE_DETACH, self.stop_event)

		self.logger.debug('NodeUnstageVolume finished successfully for request: {}'.format(reqJson))
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

		# K8s Bug Workaround: readonly flag is not sent to CSI, so we try to also infer from the AccessMode
		is_readonly = readonly or access_mode == Consts.AccessMode.MULTI_NODE_READER_ONLY

		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)

		reqJson = MessageToJson(request)
		self.logger.debug('NodePublishVolume called with request: {}'.format(reqJson))
		self.logger.debug('NodePublishVolume podInfo: {}'.format(podInfo))

		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			raise DriverError(StatusCode.NOT_FOUND, 'nvmesh volume {} was not found under /dev/nvmesh/'.format(nvmesh_volume_name))

		requested_mount_permissions, mount_options = self._parse_mount_options(volume_capability.mount)

		if is_readonly:
			mount_options.append('ro')

		if access_type == Consts.VolumeAccessType.BLOCK:
			# create an empty file for bind mount of a block device
			with open(publish_path, 'w'):
				pass

			# bind directly from block device to publish_path
			self.logger.debug('NodePublishVolume trying to bind mount as block device {} to {}'.format(block_device_path, publish_path))
			FileSystemManager.bind_mount(source=block_device_path, target=publish_path, mount_options=mount_options)
		else:
			self.logger.debug('NodePublishVolume creating directory for bind mount at {}'.format(publish_path))
			# create an empty dir for bind mount of a file system
			if not os.path.isdir(publish_path):
				os.makedirs(publish_path)

			self.logger.debug('NodePublishVolume trying to bind mount {} to {}'.format(staging_target_path, publish_path))
			FileSystemManager.bind_mount(source=staging_target_path, target=publish_path, mount_options=mount_options)

		if not is_readonly:
			FileSystemManager.chmod(requested_mount_permissions or Consts.DEFAULT_MOUNT_PERMISSIONS, publish_path)

		self.logger.debug('NodePublishVolume finished successfully for request: {}'.format(reqJson))
		return NodePublishVolumeResponse()

	@CatchServerErrors
	def NodeUnpublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'target_path'])

		target_path = request.target_path

		reqJson = MessageToJson(request)
		self.logger.debug('NodeUnpublishVolume called with request: {}'.format(reqJson))

		if not os.path.exists(target_path):
			self.logger.debug('NodeUnpublishVolume: target_path {} not found - nothing to do'.format(target_path))
			return NodeUnpublishVolumeResponse()

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
		elif os.path.isfile(target_path):
			self.logger.debug('NodeUnpublishVolume removing publish file: {}'.format(target_path))
			os.remove(target_path)

		self.logger.debug('NodeUnpublishVolume finished successfully for request: {}'.format(reqJson))
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
		required_bytes = request.capacity_range.required_bytes
		access_type = self._get_block_or_mount_volume(request)

		reqJson = MessageToJson(request)
		self.logger.debug('NodeExpandVolume called with request: {}'.format(reqJson))
		self.logger.debug('NodeExpandVolume New size: {} ({} bytes)'.format(Utils.format_as_GiB(required_bytes), required_bytes))

		zone, nvmesh_vol_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)
		block_device_path = Utils.get_nvmesh_block_device_path(nvmesh_vol_name)
		self.logger.debug('NodeExpandVolume zone: {} nvmesh_vol_name: {} block_device_path: {}'.format(zone, nvmesh_vol_name, block_device_path))

		# wait for block device to expand
		self.wait_for_nvmesh_block_device_extend(block_device_path, required_bytes)

		target_device = block_device_path

		# Check if using dmcrypt
		fs_type = FileSystemManager.get_fs_type(block_device_path)
		if fs_type == FSType.CRYPTO_LUKS:
			self.logger.debug('NodeExpandVolume device is encrypted with LUKS fs_type={}'.format(fs_type))

			# with a dmcrypt volume we should run the FileSystem expand tool (e.g. xfs_growfs) on the mapped device at /dev/mapper/{vol}
			# set the target_device to /dev/mapper/{vol}
			target_device = DMCrypt.get_mapped_device_path(nvmesh_vol_name)

			# Resize the LUKS partition
			self.resize_dmcrypt_device(target_device, required_bytes)

			# we should run get_fs_type again on the /dev/mapper/{vol} path to get the "actual" FileSystem type (e.g. xfs/ext4)
			fs_type = FileSystemManager.get_fs_type(target_device)

		self.logger.debug('device {} fs_type={}'.format(target_device, fs_type))

		# Check if a Filesystem volume
		if access_type == Consts.VolumeAccessType.MOUNT:
			# Resize the FileSystem
			exit_code, stdout, stderr = FileSystemManager.expand_file_system(target_device, fs_type)
			fs_size = FileSystemManager.get_file_system_size(mount_path=volume_path)

			if exit_code != 0:
				raise DriverError(StatusCode.INTERNAL, 'Failed to expand FileSystem {} on block device {} to {} current size is {}'.format(
					fs_type, target_device, Utils.format_as_GiB(required_bytes), Utils.format_as_GiB(fs_size)))
			else:
				self.logger.debug('Resized File System of type {} on volume {} to {}'.format(fs_type, target_device, Utils.format_as_GiB(fs_size)))
				self.logger.debug('NodeExpandVolumeResponse - Resized File System on {} finished successfully'.format(target_device))
		return NodeExpandVolumeResponse()

	def resize_dmcrypt_device(self, target_device, required_bytes, attempts_left=20):
		self.logger.debug('NodeExpandVolume Resizing the LUKS Partition on {}'.format(target_device))

		while attempts_left:
			attempts_left = attempts_left - 1
			dmcrypt_original_size = FileSystemManager.get_block_device_size_bytes(target_device)

			exit_code, stdout, stderr = FileSystemManager.expand_file_system(target_device, FSType.CRYPTO_LUKS)
			dmcrypt_device_size = FileSystemManager.get_block_device_size_bytes(target_device)
			if dmcrypt_device_size > dmcrypt_original_size:
				self.logger.debug('Resized dmcrypt LUKS partition on {} to {} ({} bytes)'.format(target_device, Utils.format_as_GiB(dmcrypt_device_size), dmcrypt_device_size))
				break
			else:
				self.logger.debug('Resizing dmcrypt {} did not update the device size waiting for 2 seconds and trying again'.format(target_device))
				self.stop_event.wait(2)
		if not attempts_left:
			raise DriverError(StatusCode.INTERNAL, 'Failed to resize LUKS device {} to {}'.format(target_device, Utils.format_as_GiB(required_bytes)))

	def wait_for_nvmesh_block_device_extend(self, block_device_path, required_bytes, attempts_left=20):
		while attempts_left:
			nvmesh_device_size_bytes = FileSystemManager.get_block_device_size_bytes(block_device_path)
			if nvmesh_device_size_bytes == required_bytes:
				self.logger.warning('NVMesh block device resized to {} ({} bytes)'.format(Utils.format_as_GiB(nvmesh_device_size_bytes), required_bytes))
				break

			self.logger.warning('NVMesh block device size is still {} but expected {}'.format(nvmesh_device_size_bytes, required_bytes))
			attempts_left = attempts_left - 1
			self.stop_event.wait(2)

		if not attempts_left:
			raise DriverError(StatusCode.INTERNAL, 'Back-Off waiting for NVMesh block device {} to resize to {} ({} bytes) current size {} ({} bytes)'.format(
				block_device_path, 
				Utils.format_as_GiB(required_bytes),
				required_bytes, 
				Utils.format_as_GiB(nvmesh_device_size_bytes),
				nvmesh_device_size_bytes,
				))

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
			self.zone = self.get_node_zone_or_wait(self.node_id)
			topology_key = TopologyUtils.get_topology_key()
			topology_info[topology_key] = self.zone
		elif Config.TOPOLOGY_TYPE == Consts.TopologyType.SINGLE_ZONE_CLUSTER:
			topology_key = TopologyUtils.get_topology_key()
			topology_info[topology_key] = Consts.SINGLE_CLUSTER_ZONE_NAME
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Unsupported Config.TOPOLOGY_TYPE of %s' % Config.TOPOLOGY_TYPE)

		self.logger.debug('Node topology: %s' % topology_info)
		return Topology(segments=topology_info)


	def get_node_zone_or_wait(self, node_id):
		attempts_left = 6
		backoff = BackoffDelayWithStopEvent(self.stop_event, initial_delay=2, factor=2, max_delay=60)
		while attempts_left > 0:
			try:
				return TopologyUtils.get_node_zone(node_id)
			except NodeNotFoundInTopology:
				attempts_left = attempts_left - 1
				self.logger.debug('Could not find this node (%s) in the topology. waiting %d seconds before trying again' % (node_id, backoff.current_delay))
				stopped_flag = backoff.wait()
				if stopped_flag:
					raise DriverError(StatusCode.INTERNAL, 'Driver stopped')

		raise DriverError(StatusCode.INTERNAL, 'Could not find node %s in any of the zones in the topology. Check nvmesh-csi-topology ConfigMap' % node_id)

	def _parse_mount_options(self, mount_request):
		mount_options = []
		permissions = None

		if mount_request.mount_flags:
			for flag in mount_request.mount_flags:
				if flag.startswith('nvmesh:chmod=') or flag.startswith('nvmesh:permissions='):
					permissions = flag.split('=')[1]
				else:
					mount_options.append(flag)

		return permissions, mount_options

	def open_or_create_dmcrypt_device(self, nvmesh_volume_name, key, volume_context):
		nvmesh_dev_path = Utils.get_nvmesh_block_device_path(nvmesh_volume_name)

		self.logger.debug('dmCrypt: Checking if device {} is encrypted'.format(nvmesh_dev_path))
		already_encrypted, err = DMCrypt.is_device_encrypted(nvmesh_dev_path, key)
		if err:
			if err.exit_code == DMCrypt.WRONG_KEY:
				raise DriverError(StatusCode.PERMISSION_DENIED, err)
			else:
				raise DriverError(StatusCode.INTERNAL, err)

		if already_encrypted:
			self.logger.debug('dmCrypt: device {} already encrypted'.format(nvmesh_dev_path))
		else:
			self.logger.debug('dmCrypt: device {} is not encrypted'.format(nvmesh_dev_path))
			dmcrypt_format_flags = self.parse_dmcrypt_flags_from_storage_class(volume_context)
			self.logger.debug('dmCrypt: Formatting {} with Luks'.format(nvmesh_dev_path))
			err = DMCrypt.luksFormat(nvmesh_dev_path, key, dmcrypt_format_flags)
			if err:
				raise DriverError(StatusCode.INTERNAL, err)

		self.logger.debug('dmCrypt: DEBUG device {} is_open={}'.format(nvmesh_volume_name, DMCrypt.is_open(nvmesh_volume_name)))

		self.logger.debug('dmCrypt: Opening encrypted device ' + nvmesh_dev_path + ' as /dev/mapper/' + nvmesh_volume_name)
		err = DMCrypt.open(nvmesh_dev_path, nvmesh_volume_name, key)
		if err:
			raise DriverError(StatusCode.INTERNAL, err)

	def close_dmcrypt_device(self, nvmesh_volume_name):
		print('dmCrypt: closing device ' + nvmesh_volume_name)
		err = DMCrypt.close(nvmesh_volume_name)
		if err:
			raise DriverError(StatusCode.INTERNAL, err)
	
	def parse_dmcrypt_flags_from_storage_class(self, volume_context):
		dmcrypt_format_flags = {}
		supported_flags = ['type', 'cipher']

		for flag in supported_flags:
			value = volume_context.get('dmcrypt/' + flag, '')
			
			if value:
				dmcrypt_format_flags['--' + flag] = value

		return dmcrypt_format_flags