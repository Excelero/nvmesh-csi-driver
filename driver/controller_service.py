import datetime
import json
import logging
import uuid
from threading import Thread

from google.protobuf.json_format import MessageToJson, MessageToDict
from grpc import StatusCode

from NVMeshSDK.ConnectionManager import ManagementTimeout
from NVMeshSDK.Entities.Volume import Volume as NVMeshVolume
from NVMeshSDK.Consts import RAIDLevels, EcSeparationTypes
from NVMeshSDK.MongoObj import MongoObj
from common import CatchServerErrors, DriverError, Utils
import consts as Consts
from csi.csi_pb2 import Volume, CreateVolumeResponse, DeleteVolumeResponse, ValidateVolumeCapabilitiesResponse, ListVolumesResponse, ControllerGetCapabilitiesResponse, ControllerServiceCapability, ControllerExpandVolumeResponse, Topology
from csi.csi_pb2_grpc import ControllerServicer
from config import Config, get_config_json
from topology_service import TopologyService
from persistency import VolumesCache
from sdk_helper import NVMeshSDKHelper
from topology_utils import TopologyUtils, VolumeAPIPool, ZoneSelectionManager


class NVMeshControllerService(ControllerServicer):
	def __init__(self, logger, stop_event):
		ControllerServicer.__init__(self)
		self.logger = logger
		self.stop_event = stop_event

		if Config.TOPOLOGY_TYPE == Consts.TopologyType.SINGLE_ZONE_CLUSTER:
			api = NVMeshSDKHelper.init_session_with_single_management(self.logger)
			management_version_info = NVMeshSDKHelper.get_management_version(api)
			self._log_mgmt_version_info(management_version_info)

		self.logger.info('Config: {}'.format(get_config_json()))
		self.volume_to_zone_mapping = VolumesCache()
		self.topology_service = TopologyService()
		self.topology_service_thread = None
		self.start_topology_service_thread()

	@CatchServerErrors
	def CreateVolume(self, request, context):
		request_uuid = uuid.uuid4()
		Utils.validate_param_exists(request, 'name')
		request_name = request.name
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(request_name)

		volume_cache = self.volume_to_zone_mapping.get_or_create_new(nvmesh_vol_name)

		with volume_cache.lock:
			log = self.logger.getChild("CreateVolume:%s(uuid:%s)" % (request_name, request_uuid))

			if volume_cache.csi_volume:
				if volume_cache.csi_volume.capacity_bytes != self._parse_required_capacity(request.capacity_range):
					raise DriverError(StatusCode.FAILED_PRECONDITION, 'Volume already exists with different capacity')

				log.info('Returning volume from cache')
				return CreateVolumeResponse(volume=volume_cache.csi_volume)

			csiVolume = self.do_create_volume(log, nvmesh_vol_name, request)
			volume_cache.csi_volume = csiVolume
			return CreateVolumeResponse(volume=csiVolume)

	def do_create_volume(self, log, nvmesh_vol_name, request):
		# UNUSED - secrets = request.secrets
		# UNUSED - volume_content_source = request.volume_content_source
		reqDict = MessageToDict(request)
		reqJson = MessageToJson(request)
		log.debug('request: {}'.format(reqJson))
		capacity = self._parse_required_capacity(request.capacity_range)
		csi_metadata = self._build_metadata_field(reqDict)
		nvmesh_params = self._handle_volume_req_parameters(reqDict, log)
		topology_requirements = reqDict.get('accessibilityRequirements')

		volume = NVMeshVolume(
			name=nvmesh_vol_name,
			capacity=capacity,
			csi_metadata=csi_metadata,
			**nvmesh_params
		)

		allowed_zones = TopologyUtils.get_allowed_zones_from_topology(topology_requirements)

		log.debug('Allowed zones: %s' % allowed_zones)
		zone = self.create_volume_on_a_valid_zone(volume, allowed_zones, log)

		# we return the zone:nvmesh_vol_name to the CO
		# all subsequent requests for this volume will have volume_id of the zone:nvmesh_vol_name
		volume_id_for_co = Utils.nvmesh_vol_name_to_co_id(nvmesh_vol_name, zone)
		topology_key = TopologyUtils.get_topology_key()
		volume_topology = Topology(segments={topology_key: zone})
		csiVolume = Volume(volume_id=volume_id_for_co, capacity_bytes=capacity, accessible_topology=[volume_topology])
		return csiVolume

	def create_volume_on_a_valid_zone(self, volume, zones, log):
		zones_left = set(zones)
		while True:
			selected_zone = ZoneSelectionManager.pick_zone(list(zones_left))
			zones_left.remove(selected_zone)

			try:
				is_zone_disabled = self.topology_service.topology.is_zone_disabled(selected_zone)
				if is_zone_disabled:
					raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Zone {} is disabled. Skipping this zone'.format(selected_zone))

				self.create_volume_in_zone(volume, selected_zone, log)
				return selected_zone
			except DriverError as ex:
				if ex.code != StatusCode.RESOURCE_EXHAUSTED:
					raise

				log.warning(ex.message)
				if len(zones_left):
					log.info('retrying volume creation for {} on zones: {}'.format(volume.name, ','.join(list(zones_left))))
				else:
					raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Failed to create volume on all zones ({})'.format(', '.join(zones)))

	def create_volume_in_zone(self, volume, zone, log):
		csi_metadata = volume.csi_metadata
		csi_metadata['zone'] = zone
		log.info('Creating volume {} in zone {}'.format(volume.name, zone))
		log.debug('Creating volume: {}'.format(str(volume)))
		time1 = datetime.datetime.now()

		data = None
		try:
			volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)
			err, data = volume_api.save([volume])
			# this is only required for printing informative logs
			mgmt_server = volume_api.managementConnection.managementServer
		except ManagementTimeout as ex:
			err = ex
			api_params = TopologyUtils.get_api_params(zone)
			mgmt_server = api_params['managementServers']

		time2 = datetime.datetime.now()
		self._handle_create_volume_errors(err, data, volume, zone, mgmt_server, log)

	def _handle_create_volume_errors(self, err, data, volume, zone, mgmt_server, log):
		failed_to_create_msg = 'Failed to create volume {vol_name} in zone {zone} ({mgmt})'.format(
			vol_name=volume.name,
			zone=zone,
			mgmt=mgmt_server)

		if err:
			# Failed to Connect to Management or other HTTP Error
			self.topology_service.topology.disable_zone(zone)
			raise DriverError(StatusCode.RESOURCE_EXHAUSTED, '{} Error: {}'.format(failed_to_create_msg, err))
		else:
			# management returned a response
			self.topology_service.topology.make_sure_zone_enabled(zone)

			if not type(data) == list or not data[0]['success']:
				volume_already_exists = 'Name already Exists' in data[0]['error'] or 'duplicate key error' in json.dumps(data[0]['error'])
				if volume_already_exists:
					existing_capacity = self._get_nvmesh_volume_capacity(volume.name, log, zone)
					if volume.capacity == existing_capacity:
						# Idempotency - same Name same Capacity - return success
						pass
					else:
						raise DriverError(StatusCode.ALREADY_EXISTS, 'Volume already exists with different capacity. Details: {}'.format(data))
				else:
					raise DriverError(StatusCode.RESOURCE_EXHAUSTED, failed_to_create_msg + '. Response: {} Volume Requested: {}'.format(data, str(volume)))

	def _build_metadata_field(self, req_dict):
		capabilities = req_dict['volumeCapabilities']

		csi_metadata = {
			'csi_name': req_dict['name'],
		}

		for param_name in req_dict['parameters'].keys():
			if 'csi.storage.k8s.io' in param_name:
				csi_metadata[param_name] = req_dict['parameters'][param_name]

		for capability in capabilities:
			if 'mount' in capability:
				csi_metadata['fsType'] = capability['mount'].get('fsType', Consts.FSType.EXT4)
				csi_metadata['volumeMode'] = 'mount'
			elif 'block' in capability:
				csi_metadata['volumeMode'] = 'block'

			if 'accessMode' in capability:
				access_mode = capability['accessMode']['mode']
				if Consts.AccessMode.fromCsiString(access_mode) not in Consts.AccessMode.allowed_access_modes():
					self.logger.warning('Requested mode {} is not enforced by NVMesh Storage backend'.format(access_mode))

		if 'fsType' in csi_metadata and 'block' in csi_metadata:
			raise DriverError(
				StatusCode.INVALID_ARGUMENT,
				'Error: Contradicting capabilities both Block Volume and FileSystem Volume were requested for volume {}. request: {}'
				.format(req_dict['name'], req_dict))

		csi_metadata = Utils.sanitize_json_object_keys(csi_metadata)
		return csi_metadata

	def _handle_volume_req_parameters(self, req_dict, log):
		parameters = req_dict['parameters']

		for param_name in parameters.keys():
			if 'csi.storage.k8s.io' in param_name:
				del parameters[param_name]

		nvmesh_params = {}
		log.debug('create volume parameters: {}'.format(parameters))

		if 'vpg' in parameters:
			log.debug('Creating Volume from VPG {}'.format(parameters['vpg']))
			nvmesh_params['VPG'] = parameters['vpg']
		else:
			log.debug('Creating without VPG')
			for param in parameters:
				nvmesh_params[param] = parameters[param]

			self._handle_non_vpg_params(nvmesh_params)

		# For both VPG and non-VPG
		nvmesh_params['relativeRebuildPriority'] = nvmesh_params.get('relativeRebuildPriority', 10)

		self.logger.debug('nvmesh_params = {}'.format(nvmesh_params))
		return nvmesh_params

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
			nvmesh_params['enableCrcCheck'] = Utils.parseBoolean(nvmesh_params.get('enableCrcCheck', False))

		if raid_level == RAIDLevels.ERASURE_CODING:
			nvmesh_params['dataBlocks'] = int(nvmesh_params.get('dataBlocks', 8))
			nvmesh_params['parityBlocks'] = int(nvmesh_params.get('parityBlocks', 2))
			nvmesh_params['protectionLevel'] = nvmesh_params.get('protectionLevel', EcSeparationTypes.FULL)
			nvmesh_params['stripeSize'] = int(nvmesh_params.get('stripeSize', 32))
			nvmesh_params['stripeWidth'] = int(nvmesh_params.get('stripeWidth', 1))
			nvmesh_params['enableCrcCheck'] = Utils.parseBoolean(nvmesh_params.get('enableCrcCheck', True))

	@CatchServerErrors
	def DeleteVolume(self, request, context):
		Utils.validate_param_exists(request, 'volume_id')

		volume_id = request.volume_id
		log = self.logger.getChild("DeleteVolume-%s" % volume_id)

		zone, nvmesh_vol_name = Utils.zone_and_vol_name_from_co_id(volume_id)
		#secrets = request.secrets

		volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)

		err, out = volume_api.delete([NVMeshVolume(_id=nvmesh_vol_name)])
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

		self.volume_to_zone_mapping.remove(nvmesh_vol_name)

		return DeleteVolumeResponse()

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

		# TODO: we should probably iterate over all management servers and return all volumes while populating the volume.accessible_topology field
		zone = ''
		volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)
		err, nvmeshVolumes = volume_api.get(projection=projection, page=page, count=count)

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
		#list_volumes = buildCapability(ControllerServiceCapability.RPC.LIST_VOLUMES)
		expand_volume = buildCapability(ControllerServiceCapability.RPC.EXPAND_VOLUME)

		# Not Implemented
		# get_capacity = buildCapability(ControllerServiceCapability.RPC.GET_CAPACITY)
		# create_delete_snapshot = buildCapability(ControllerServiceCapability.RPC.CREATE_DELETE_SNAPSHOT)
		# list_snapshots = buildCapability(ControllerServiceCapability.RPC.LIST_SNAPSHOTS)
		# clone_volume = buildCapability(ControllerServiceCapability.RPC.CLONE_VOLUME)

		capabilities = [
			create_delete_volume,
			#list_volumes,
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
		zone, nvmesh_vol_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)
		log = logging.getLogger('ExpandVolume-%s' % nvmesh_vol_name)

		volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)
		volume = self.get_nvmesh_volume(volume_api, nvmesh_vol_name)

		# Call Node Expansion Method to Expand a FileSystem
		# For a Block Device there is no need to do anything on the node
		node_expansion_required = True if 'fsType' in volume.csi_metadata else False

		# Extend Volume
		volume.capacity = capacity_in_bytes

		self.logger.debug("ControllerExpandVolume volume={}".format(str(volume)))
		err, out = volume_api.update([volume])

		if err:
			raise DriverError(StatusCode.NOT_FOUND, err)

		self.logger.debug("ControllerExpandVolumeResponse: capacity_in_bytes={}, node_expansion_required={}".format(capacity_in_bytes, node_expansion_required))
		return ControllerExpandVolumeResponse(capacity_bytes=capacity_in_bytes, node_expansion_required=node_expansion_required)

	def get_nvmesh_volume(self, volume_api, nvmesh_vol_name,):
		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]

		err, out = volume_api.get(filter=filterObj)
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

	def _get_nvmesh_volume_capacity(self, nvmesh_vol_name, log, zone=None):
		volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)

		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		projection = [MongoObj(field='_id', value=1), MongoObj(field='capacity', value=1)]

		err, out = volume_api.get(filter=filterObj, projection=projection)
		if err or not len(out):
			raise DriverError(StatusCode.INTERNAL, err)

		return out[0].capacity

	def _get_volume_by_name(self, volume_id, zone, log):
		volume_api = VolumeAPIPool.get_volume_api_for_zone(zone)

		filterObj = [MongoObj(field='_id', value=volume_id)]
		err, data = volume_api.get(filter=filterObj)
		if err:
			return err, data
		else:
			if not len(data):
				return "Could Not Find Volume {}".format(volume_id), None
			else:
				return None, data[0]

	def _log_mgmt_version_info(self, management_version_info):
		msg = "Management Version:"
		if not management_version_info:
			msg += management_version_info
		else:
			for key, value in management_version_info.iteritems():
				msg += "\n{}={}".format(key, value)
		self.logger.info(msg)

	def start_topology_service_thread(self):
		self.topology_service_thread = Thread(name='topology-service-thread', target=self.topology_service.run)
		self.topology_service_thread.start()