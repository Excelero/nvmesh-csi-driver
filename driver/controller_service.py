import json
import time

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from google.protobuf.json_format import MessageToJson, MessageToDict
from grpc import StatusCode

from NVMeshSDK.APIs.TargetAPI import TargetAPI
from NVMeshSDK.Entities.Volume import Volume as NVMeshVolume
from NVMeshSDK.Consts import RAIDLevels, EcSeparationTypes
from NVMeshSDK import Consts as NVMeshConsts
from NVMeshSDK.MongoObj import MongoObj
from common import CatchServerErrors, DriverError, Utils, NVMeshSDKHelper
import consts as Consts
from csi.csi_pb2 import Volume, CreateVolumeResponse, DeleteVolumeResponse, ControllerPublishVolumeResponse, ControllerUnpublishVolumeResponse, \
	ValidateVolumeCapabilitiesResponse, ListVolumesResponse, ControllerGetCapabilitiesResponse, ControllerServiceCapability, ControllerExpandVolumeResponse
from csi.csi_pb2_grpc import ControllerServicer
from config import config_loader


class NVMeshControllerService(ControllerServicer):
	def __init__(self, logger):
		config_loader.load()
		ControllerServicer.__init__(self)
		self.logger = logger
		NVMeshSDKHelper.init_sdk()
		self.management_version_info = NVMeshSDKHelper.get_management_version()
		self._log_mgmt_version_info()

	@CatchServerErrors
	def CreateVolume(self, request, context):
		Utils.validate_param_exists(request, 'name')
		name = request.name
		capacity = self._parse_required_capacity(request.capacity_range)
		parameters = request.parameters

		#UNUSED - secrets = request.secrets
		#UNUSED - volume_content_source = request.volume_content_source
		#UNUSED - accessibility_requirements = request.accessibility_requirements

		reqJson = MessageToJson(request)
		self.logger.debug('create volume request: {}'.format(reqJson))
		reqDict = MessageToDict(request)
		capabilities = reqDict['volumeCapabilities']

		is_file_system = False
		is_block_device = False

		csi_metadata = {
			'csi_name': name,
			'capabilities': capabilities
		}

		for capability in capabilities:
			if 'mount' in capability:
				is_file_system = True
				csi_metadata['fsType'] = capability['mount']['fsType']
			elif 'block' in capability:
				csi_metadata['block'] = True

			if 'accessMode' in capability:
				access_mode = capability['accessMode']['mode']
				if Consts.AccessMode.fromCsiString(access_mode) not in Consts.AccessMode.allowed_access_modes():
					self.logger.warning('Requested mode {} is not enforced by NVMesh Storage backend'.format(access_mode))

		if is_file_system and is_block_device:
			raise DriverError(StatusCode.INVALID_ARGUMENT,
								'Error: Contradicting capabilities both Block Volume and FileSystem Volume were requested for volume {}. request: {}'.format(name,
																																						reqJson))

		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(name)
		nvmesh_params = {}

		self.logger.debug('create volume parameters: {}'.format(parameters))

		if 'vpg' in parameters:
			self.logger.debug('Creating Volume from VPG {}'.format(parameters['vpg']))
			nvmesh_params['VPG'] = parameters['vpg']

			# This is a workaround since the nvmesh create volume api expects a 'RAIDLevel'
			# but if 'VPG' is present 'RAIDLevel' field will be ignored
			# and the RAIDLevel will be fetched from the VPG.
			nvmesh_params['RAIDLevel'] = RAIDLevels.CONCATENATED
		else:
			self.logger.debug('Creating without VPG')
			for param in parameters:
				nvmesh_params[param] = parameters[param]

			self._handle_non_vpg_params(nvmesh_params)

		self.logger.debug('nvmesh_params = {}'.format(nvmesh_params))

		volume = NVMeshVolume(
			name=nvmesh_vol_name,
			capacity=capacity,
			csi_metadata=csi_metadata,
			**nvmesh_params
		)

		self.logger.debug('Creating volume: {}'.format(str(volume)))
		err, data = VolumeAPI().save([volume])

		if err:
			raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Error: {} Details: {} Volume Requested: {}'.format(err, data, str(volume)))
		elif not type(data) == list or not data[0]['success']:
			if 'Name already Exists' in data[0]['error']:
				existing_capacity = self._get_nvmesh_volume_capacity(nvmesh_vol_name)
				if capacity == existing_capacity:
					# Idempotency - same Name same Capacity - return success
					pass
				else:
					raise DriverError(StatusCode.ALREADY_EXISTS, 'Error: {} Details: {}'.format(err, data))
			else:
				raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Error: {} Details: {}'.format(err, data))

		err, details = self._wait_for_volume_status(volume._id, NVMeshConsts.VolumeStatuses.ONLINE)

		if err:
			if err == 'Timed out Waiting for Volume to be Online':
				raise DriverError(StatusCode.FAILED_PRECONDITION, 'Error: {} Details: {}'.format(err, details))
			else:
				raise DriverError(StatusCode.INVALID_ARGUMENT, err)
		else:
			self.logger.debug(details)

		# we return the nvmesh_vol_name that we created to the CO
		# all subsequent requests for this volume will have volume_id of the nvmesh volume name
		csiVolume = Volume(volume_id=nvmesh_vol_name, capacity_bytes=capacity)
		return CreateVolumeResponse(volume=csiVolume)

	def _handle_non_vpg_params(self, nvmesh_params):
		# parse raidLevel
		if 'raidLevel' in nvmesh_params:
			nvmesh_params['RAIDLevel'] = self._parse_raid_type(nvmesh_params['raidLevel'])
			del nvmesh_params['raidLevel']
		else:
			# default volume type
			nvmesh_params['RAIDLevel'] = RAIDLevels.CONCATENATED

		raid_level = nvmesh_params['RAIDLevel']

		if raid_level in [RAIDLevels.STRIPED_RAID_0, RAIDLevels.STRIPED_AND_MIRRORED_RAID_10]:
			nvmesh_params['stripeWidth'] = int(nvmesh_params.get('stripeWidth', 2))
			nvmesh_params['stripeSize'] = int(nvmesh_params.get('stripeSize', 32))

		if raid_level in [RAIDLevels.MIRRORED_RAID_1, RAIDLevels.STRIPED_AND_MIRRORED_RAID_10]:
			nvmesh_params['numberOfMirrors'] = 1

		if raid_level == RAIDLevels.ERASURE_CODING:
			nvmesh_params['dataBlocks'] = int(nvmesh_params.get('dataBlocks', 8))
			nvmesh_params['parityBlocks'] = int(nvmesh_params.get('parityBlocks', 2))
			nvmesh_params['protectionLevel'] = nvmesh_params.get('protectionLevel', EcSeparationTypes.FULL)
			nvmesh_params['stripeSize'] = int(nvmesh_params.get('stripeSize', 32))

	def _wait_for_volume_status(self, volume_id, status):

		volume_status = None
		volume = None
		attempts = 15

		while volume_status != status and attempts > 0:
			err, volume = self._get_volume_by_name(volume_id)
			if err:
				if 'Could Not Find Volume' not in err:
					return err, volume

			if volume and volume.status == status:
				return None, volume

			attempts -= 1
			time.sleep(1)

		return 'Timed out Waiting for Volume to be Online', volume

	@CatchServerErrors
	def DeleteVolume(self, request, context):
		Utils.validate_param_exists(request, 'volume_id')

		volume_id = request.volume_id
		nvmesh_vol_name = volume_id
		#secrets = request.secrets

		err, out = VolumeAPI().delete([NVMeshVolume(_id=nvmesh_vol_name)])
		if err:
			self.logger.error(err)
			raise DriverError(StatusCode.INTERNAL, err)

		self.logger.debug(out)

		if not out[0]['success']:
			err = out[0]['error']

			if err == "Couldn't find the specified volume":
				# Idempotency - Trying to remove a Volume that doesn't exists, perhaps already deleted
				# should return success
				pass
			else:
				raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return DeleteVolumeResponse()

	@CatchServerErrors
	def ControllerPublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['node_id', 'volume_id', 'volume_capability'])

		nvmesh_vol_name = request.volume_id
		self._validate_volume_exists(nvmesh_vol_name)
		self._validate_node_exists(request.node_id)


		return ControllerPublishVolumeResponse()

	@CatchServerErrors
	def ControllerUnpublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['node_id', 'volume_id'])

		nvmesh_vol_name = request.volume_id
		self._validate_volume_exists(nvmesh_vol_name)
		self._validate_node_exists(request.node_id)


		return ControllerUnpublishVolumeResponse()

	@CatchServerErrors
	def ValidateVolumeCapabilities(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'volume_capabilities'])
		nvmesh_vol_name = request.volume_id
		#UNUSED - capabilities = request.volume_capabilities

		# always return True
		confirmed = ValidateVolumeCapabilitiesResponse.Confirmed(volume_capabilities=request.volume_capabilities)
		return ValidateVolumeCapabilitiesResponse(confirmed=confirmed)

	@CatchServerErrors
	def ListVolumes(self, request, context):
		max_entries = request.max_entries
		starting_token = request.starting_token

		try:
			page = int(starting_token or 0)
		except ValueError:
			raise DriverError(StatusCode.ABORTED, "Invalid starting_token")

		if starting_token and not max_entries:
			raise DriverError(StatusCode.ABORTED, "Invalid starting_token")

		count = max_entries or 0

		projection = [
			MongoObj(field='_id', value=1),
			MongoObj(field='capacity', value=1)
		]

		err, nvmeshVolumes = VolumeAPI().get(projection=projection, page=page, count=count)

		if err:
			raise DriverError(StatusCode.INTERNAL, err)

		def convertNVMeshVolumeToCSIVolume(volume):
			vol = Volume(volume_id=volume._id, capacity_bytes=volume.capacity)
			return ListVolumesResponse.Entry(volume=vol)

		entries = map(convertNVMeshVolumeToCSIVolume, nvmeshVolumes)
		next_token = str(page + 1)

		if not len(entries):
			DriverError(StatusCode.ABORTED, "No more Entries")

		return ListVolumesResponse(entries=entries, next_token=next_token)

	@CatchServerErrors
	def GetCapacity(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def ControllerGetCapabilities(self, request, context):
		def buildCapability(capabilityType):
			return ControllerServiceCapability(rpc=ControllerServiceCapability.RPC(type=capabilityType))

		create_delete_volume = buildCapability(ControllerServiceCapability.RPC.CREATE_DELETE_VOLUME)
		list_volumes = buildCapability(ControllerServiceCapability.RPC.LIST_VOLUMES)
		expand_volume = buildCapability(ControllerServiceCapability.RPC.EXPAND_VOLUME)

		# Not Implemented
		# get_capacity = buildCapability(ControllerServiceCapability.RPC.GET_CAPACITY)
		# create_delete_snapshot = buildCapability(ControllerServiceCapability.RPC.CREATE_DELETE_SNAPSHOT)
		# list_snapshots = buildCapability(ControllerServiceCapability.RPC.LIST_SNAPSHOTS)
		# clone_volume = buildCapability(ControllerServiceCapability.RPC.CLONE_VOLUME)

		capabilities = [
			create_delete_volume,
			list_volumes,
			expand_volume
		]

		return ControllerGetCapabilitiesResponse(capabilities=capabilities)

	@CatchServerErrors
	def CreateSnapshot(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def DeleteSnapshot(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def ListSnapshots(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def ControllerExpandVolume(self, request, context):
		capacity_in_bytes = request.capacity_range.required_bytes
		nvmesh_vol_name = request.volume_id

		volume = self.get_nvmesh_volume(nvmesh_vol_name)

		# Call Node Expansion Method to Expand a FileSystem
		# For a Block Device there is no need to do anything on the node
		node_expansion_required = True if 'fsType' in volume.csi_metadata else False

		# Extend Volume
		volume.capacity = capacity_in_bytes

		self.logger.debug("ControllerExpandVolume volume={}".format(str(volume)))
		err, out = VolumeAPI().update([volume])

		if err:
			raise DriverError(StatusCode.NOT_FOUND, err)

		self.logger.debug("ControllerExpandVolumeResponse: capacity_in_bytes={}, node_expansion_required={}".format(capacity_in_bytes, node_expansion_required))
		return ControllerExpandVolumeResponse(capacity_bytes=capacity_in_bytes, node_expansion_required=node_expansion_required)

	def get_nvmesh_volume(self, nvmesh_vol_name, minimalFields=False):
		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]

		projection = None
		if minimalFields:
			projection = [
				MongoObj(field='_id', value=1),
				MongoObj(field='capacity', value=1),
				MongoObj(field='status', value=1),
				MongoObj(field='csi_metadata', value=1)
			]

		err, out = VolumeAPI().get(filter=filterObj, projection=projection)
		if err:
			raise DriverError(StatusCode.INTERNAL, err)
		if not isinstance(out, list):
			raise DriverError(StatusCode.INTERNAL, out)
		if not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Volume {} Could not be found'.format(nvmesh_vol_name))

		return out[0]

	def _parse_raid_type(self, raid_type_string):
		raid_type_string = raid_type_string.lower()

		raid_converter = {
			'concatenated': RAIDLevels.CONCATENATED,
			'lvm': RAIDLevels.CONCATENATED,
			'jbod': RAIDLevels.CONCATENATED,
			'mirrored': RAIDLevels.MIRRORED_RAID_1,
			'raid1': RAIDLevels.MIRRORED_RAID_1,
			'raid10': RAIDLevels.STRIPED_AND_MIRRORED_RAID_10,
			'raid0': RAIDLevels.STRIPED_RAID_0,
			'ec': RAIDLevels.ERASURE_CODING
		}

		if raid_type_string not in raid_converter:
			raise ValueError('Unknown RAID Type %s' % raid_type_string)

		parsed_value = raid_converter[raid_type_string]
		return parsed_value

	def _parse_required_capacity(self, capacity_range):
		if capacity_range.required_bytes:
			return capacity_range.required_bytes
		elif capacity_range.limit_bytes:
			return capacity_range.limit_bytes
		else:
			return Consts.DEFAULT_VOLUME_SIZE
			#raise DriverError(StatusCode.INVALID_ARGUMENT, "at least one of capacity_range.required_bytes, capacity_range.limit_bytes must be set")

	def _get_nvmesh_volume_capacity(self, nvmesh_vol_name):
		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		projection = [MongoObj(field='_id', value=1), MongoObj(field='capacity', value=1)]

		err, out = VolumeAPI().get(filter=filterObj, projection=projection)
		if err or not len(out):
			raise DriverError(StatusCode.INTERNAL, err)

		return out[0].capacity

	def _validate_volume_exists(self, nvmesh_vol_name):
		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		projection = [MongoObj(field='_id', value=1)]

		err, out = VolumeAPI().get(filter=filterObj, projection=projection)
		if err or not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Volume with id {}'.format(nvmesh_vol_name))

	def _validate_node_exists(self, node_id):
		filterObj = [MongoObj(field='node_id', value=node_id)]
		projection = [MongoObj(field='_id', value=1)]

		err, matches = TargetAPI().get(filter=filterObj, projection=projection)
		if err or not len(matches):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Node with id {}'.format(node_id))

	def _get_volume_by_name(self, volume_id):
		filterObj = [MongoObj(field='_id', value=volume_id)]
		err, data = VolumeAPI().get(filter=filterObj)
		if err:
			return err, data
		else:
			if not len(data):
				return "Could Not Find Volume {}".format(volume_id), None
			else:
				return None, data[0]

	def _log_mgmt_version_info(self):
		msg = "Management Version:"
		if not self.management_version_info:
			msg += self.management_version_info
		else:
			for key, value in self.management_version_info.iteritems():
				msg += "\n{}={}".format(key, value)
		self.logger.info(msg)



