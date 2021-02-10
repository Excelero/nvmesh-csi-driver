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
	ValidateVolumeCapabilitiesResponse, ListVolumesResponse, ControllerGetCapabilitiesResponse, ControllerServiceCapability, ControllerExpandVolumeResponse, Topology
from csi.csi_pb2_grpc import ControllerServicer
from config import config_loader, Config
from topology import TopologyUtils, ZoneSelectionManager


class NVMeshControllerService(ControllerServicer):
	def __init__(self, logger):
		config_loader.load()
		ControllerServicer.__init__(self)
		self.logger = logger
		if not Config.MULTIPLE_NVMESH_BACKENDS:
			api = NVMeshSDKHelper.init_sdk(self.logger)
			management_version_info = NVMeshSDKHelper.get_management_version(api)
			self._log_mgmt_version_info(management_version_info)

		self.vol_to_zone_mapping = {}

	@CatchServerErrors
	def CreateVolume(self, request, context):
		self._print_context_metadata(context)
		Utils.validate_param_exists(request, 'name')
		name = request.name
		parameters = request.parameters
		#UNUSED - secrets = request.secrets
		#UNUSED - volume_content_source = request.volume_content_source

		reqDict = MessageToDict(request)
		reqJson = MessageToJson(request)
		self.logger.debug('create volume request: {}'.format(reqJson))

		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(name)
		capacity = self._parse_required_capacity(request.capacity_range)
		csi_metadata = self._build_metadata_field(reqDict)
		nvmesh_params = self._handle_volume_req_parameters(reqDict)

		topology_requirements = reqDict.get('accessibilityRequirements')
		volume_api, zone = self._get_api_and_zone_from_topology(topology_requirements)
		csi_metadata['zone'] = zone

		volume = NVMeshVolume(
			name=nvmesh_vol_name,
			capacity=capacity,
			csi_metadata=csi_metadata,
			**nvmesh_params
		)

		self.logger.debug('Creating volume: {}'.format(str(volume)))
		err, data = volume_api.save([volume])

		self._handle_create_volume_errors(err, data, volume, zone)

		err, details = self._wait_for_volume_status(volume._id, NVMeshConsts.VolumeStatuses.ONLINE, zone)

		if err:
			if err == 'Timed out Waiting for Volume to be Online':
				raise DriverError(StatusCode.FAILED_PRECONDITION, 'Error: {} Details: {}'.format(err, details))
			else:
				raise DriverError(StatusCode.INVALID_ARGUMENT, err)
		else:
			self.logger.debug(details)

		# we return the zone:nvmesh_vol_name to the CO
		# all subsequent requests for this volume will have volume_id of the zone:nvmesh_vol_name
		volume_id_for_co = Utils.nvmesh_vol_name_to_co_id(nvmesh_vol_name, zone)
		volume_topology = Topology(segments={Consts.TopologyKey.ZONE: zone})
		csiVolume = Volume(volume_id=volume_id_for_co, capacity_bytes=capacity, accessible_topology=[volume_topology])
		return CreateVolumeResponse(volume=csiVolume)

	def _get_api_and_zone_from_topology(self, topology_requirements):
		self.logger.debug('CreateVolume received topology requirements {}'.format(topology_requirements))

		if not topology_requirements:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Config.TOPOLOGY_TYPE = %s but received no topology info' % Config.TOPOLOGY_TYPE)

		if Config.TOPOLOGY_TYPE == Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS:
			zone = self._get_zone_from_topology(topology_requirements)
			api = self._get_volume_api_from_zone(zone)
			return api, zone

	def _get_volume_api_from_config(self):
		return {
			'managementServers': Config.MANAGEMENT_SERVERS,
			'managementProtocol': Config.MANAGEMENT_PROTOCOL,
			'user': Config.MANAGEMENT_USERNAME,
			'password': Config.MANAGEMENT_PASSWORD
		}

	def _get_volume_api_from_zone(self, zone):
		api_params = self._get_api_params_from_zone(zone)

		try:
			api = VolumeAPI(logger=self.logger, **api_params)
			return api
		except Exception as ex:
			self.logger.error('Failed to create VolumeAPI with params: {}. \nError {}'.format(api_params, ex))
			raise

	def _get_api_params_from_zone(self, zone):
		if Config.TOPOLOGY_TYPE == Consts.TopologyType.SINGLE_ZONE_CLUSTER:
			return self._get_volume_api_from_config()

		mgmt_info = TopologyUtils.get_management_info_from_zone(zone)

		if not mgmt_info:
			raise ValueError('Missing "management" key in Config.topology.zones.%s' % zone)

		managementServers = mgmt_info.get('servers')
		if not managementServers:
			raise ValueError('Missing "servers" key in Config.topology.zones.%s.management ' % zone)

		api_params = {
			'managementServers': managementServers
		}

		user = mgmt_info.get('user')
		password = mgmt_info.get('password')
		protocol = mgmt_info.get('protocol')

		if user:
			api_params['user'] = user

		if password:
			api_params['password'] = password

		if protocol:
			api_params['protocol'] = protocol

		self.logger.debug('Topology zone {} management params:  is {}'.format(zone, api_params))
		return api_params

	def _get_zone_from_topology(self, topology_requirements):
		# provisioner sidecar container should have --strict-topology flag set
		# If volumeBindingMode is Immediate - all cluster topology will be received
		# If volumeBindingMode is WaitForFirstConsumer - Only the topology of the node to which the pod is scheduled will be given
		try:
			preferred_topologies = topology_requirements.get('preferred')
			if len(preferred_topologies) == 1:
				selected_zone = preferred_topologies[0]['segments'][Consts.TopologyKey.ZONE]
			else:
				zones = map(lambda t: t['segments'][Consts.TopologyKey.ZONE], preferred_topologies)
				selected_zone = ZoneSelectionManager.pick_zone(zones)
		except Exception as ex:
			raise ValueError('Failed to get zone from topology. Error: %s' % ex)

		if not selected_zone:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Failed to get zone from topology')

		self.logger.debug('_get_zone_from_topology selected zone is {}'.format(selected_zone))
		return selected_zone

	def _handle_create_volume_errors(self, err, data, volume, zone):
		if err:
			raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Error: {} Details: {} Volume Requested: {}'.format(err, data, str(volume)))
		elif not type(data) == list or not data[0]['success']:
			if 'Name already Exists' in data[0]['error'] or 'duplicate key error' in data[0]['error']:
				existing_capacity = self._get_nvmesh_volume_capacity(volume.name, zone)
				if volume.capacity == existing_capacity:
					# Idempotency - same Name same Capacity - return success
					pass
				else:
					raise DriverError(StatusCode.ALREADY_EXISTS, 'Error: {} Details: {}'.format(err, data))
			else:
				raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Error: {} Details: {}'.format(err, data))

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

	def _handle_volume_req_parameters(self, req_dict):
		parameters = req_dict['parameters']

		for param_name in parameters.keys():
			if 'csi.storage.k8s.io' in param_name:
				del parameters[param_name]

		nvmesh_params = {}
		self.logger.debug('create volume parameters: {}'.format(parameters))

		if 'vpg' in parameters:
			self.logger.debug('Creating Volume from VPG {}'.format(parameters['vpg']))
			nvmesh_params['VPG'] = parameters['vpg']
		else:
			self.logger.debug('Creating without VPG')
			for param in parameters:
				nvmesh_params[param] = parameters[param]

			self._handle_non_vpg_params(nvmesh_params)
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
			nvmesh_params['enableCrcCheck'] = nvmesh_params.get('enableCrcCheck', False)

		if raid_level == RAIDLevels.ERASURE_CODING:
			nvmesh_params['dataBlocks'] = int(nvmesh_params.get('dataBlocks', 8))
			nvmesh_params['parityBlocks'] = int(nvmesh_params.get('parityBlocks', 2))
			nvmesh_params['protectionLevel'] = nvmesh_params.get('protectionLevel', EcSeparationTypes.FULL)
			nvmesh_params['stripeSize'] = int(nvmesh_params.get('stripeSize', 32))
			nvmesh_params['enableCrcCheck'] = nvmesh_params.get('enableCrcCheck', True)

	def _wait_for_volume_status(self, volume_id, status, zone=None):

		volume_status = None
		volume = None
		attempts = 15

		while volume_status != status and attempts > 0:
			err, volume = self._get_volume_by_name(volume_id, zone)
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
		zone, nvmesh_vol_name = Utils.zone_and_vol_name_from_co_id(volume_id)
		#secrets = request.secrets

		volume_api = self._get_volume_api_from_zone(zone)

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

	def _print_context_metadata(self, context):
		metadata = context.invocation_metadata()
		self.logger.debug(metadata)

	@CatchServerErrors
	def ControllerExpandVolume(self, request, context):
		self._print_context_metadata(context)
		capacity_in_bytes = request.capacity_range.required_bytes
		zone, nvmesh_vol_name = Utils.zone_and_vol_name_from_co_id(request.volume_id)

		if Config.TOPOLOGY_TYPE != Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS:
			volume_api = self._get_volume_api_from_config()
		else:
			volume_api = self._get_volume_api_from_zone(zone)
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

	def _get_nvmesh_volume_capacity(self, nvmesh_vol_name, zone=None):
		volume_api = self._get_volume_api(zone)

		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		projection = [MongoObj(field='_id', value=1), MongoObj(field='capacity', value=1)]

		err, out = volume_api.get(filter=filterObj, projection=projection)
		if err or not len(out):
			raise DriverError(StatusCode.INTERNAL, err)

		return out[0].capacity

	def _validate_volume_exists(self, nvmesh_vol_name, zone=None):
		volume_api = self._get_volume_api(zone)

		filterObj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		projection = [MongoObj(field='_id', value=1)]

		err, out = volume_api.get(filter=filterObj, projection=projection)
		if err or not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Volume with id {}'.format(nvmesh_vol_name))

	def _validate_node_exists(self, node_id):
		filterObj = [MongoObj(field='node_id', value=node_id)]
		projection = [MongoObj(field='_id', value=1)]

		err, matches = TargetAPI().get(filter=filterObj, projection=projection)
		if err or not len(matches):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Node with id {}'.format(node_id))

	def _get_volume_by_name(self, volume_id, zone=None):
		volume_api = self._get_volume_api(zone)

		filterObj = [MongoObj(field='_id', value=volume_id)]
		err, data = volume_api.get(filter=filterObj)
		if err:
			return err, data
		else:
			if not len(data):
				return "Could Not Find Volume {}".format(volume_id), None
			else:
				return None, data[0]

	def _get_volume_api(self, zone=None):
		if Config.TOPOLOGY_TYPE == Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS:
			volume_api = self._get_volume_api_from_zone(zone)
		else:
			volume_api = self._get_volume_api_from_config()
		return volume_api

	def _log_mgmt_version_info(self, management_version_info):
		msg = "Management Version:"
		if not management_version_info:
			msg += management_version_info
		else:
			for key, value in management_version_info.iteritems():
				msg += "\n{}={}".format(key, value)
		self.logger.info(msg)
