import json
from google.protobuf.json_format import MessageToJson, MessageToDict

from driver.common import CatchServerErrors, DriverError, Utils, Consts
from driver.csi.csi_pb2 import Volume, CreateVolumeResponse, DeleteVolumeResponse, ControllerPublishVolumeResponse, ControllerUnpublishVolumeResponse, \
	ValidateVolumeCapabilitiesResponse, ListVolumesResponse, ControllerGetCapabilitiesResponse, ControllerServiceCapability, ControllerExpandVolumeResponse
from driver.csi.csi_pb2_grpc import ControllerServicer
from managementClient.Consts import RAIDLevels
from managementClient.ManagementClientWrapper import ManagementClientWrapper
from grpc import StatusCode

class NVMeshControllerService(ControllerServicer):
	def __init__(self, logger):
		ControllerServicer.__init__(self)
		self.logger = logger
		self.mgmtClient = ManagementClientWrapper()

	@CatchServerErrors
	def CreateVolume(self, request, context):
		Utils.validate_param_exists(request, 'name')
		name = request.name
		capacity = self._parse_required_capacity(request.capacity_range)
		volume_capabilities = request.volume_capabilities
		parameters = request.parameters
		secrets = request.secrets
		volume_content_source = request.volume_content_source
		accessibility_requirements = request.accessibility_requirements

		reqJson = MessageToJson(request)
		self.logger.debug('create volume request: {}'.format(reqJson))
		reqDict = MessageToDict(request)

		description_meta_data = {
			'csi_name': name,
			'volume_capabilities': reqDict['volumeCapabilities']
		}

		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(name)
		description = json.dumps(description_meta_data)
		volume = {
			'name': nvmesh_vol_name,
			'description': description,
			'capacity': capacity,
			'RAIDLevel': RAIDLevels.CONCATENATED
		}

		self.logger.debug('create volume parameters: {}'.format(parameters))

		if 'vpg' in parameters:
			self.logger.debug('Creating Volume from VPG {}'.format(parameters['vpg']))
			volume['vpg'] = parameters['vpg']
		else:
			if 'raid_level' in parameters:
				volume['RAIDLevel'] = self._parse_raid_type(parameters['raid_level'])
			else:
				# default volume type
				volume['RAIDLevel'] = RAIDLevels.CONCATENATED

		err, details = self.mgmtClient.createVolume(volume)

		if err:
			if err == 'Could not create volume':
				if 'Name already Exists' in details:
					existing_capcity = self._get_nvmesh_volume_capacity(nvmesh_vol_name)
					if capacity == existing_capcity:
						# Idempotency - same Name same Capacity - return success
						pass
					else:
						raise DriverError(StatusCode.ALREADY_EXISTS, 'Error: {} Details: {}'.format(err, details))
				else:
					raise DriverError(StatusCode.RESOURCE_EXHAUSTED, 'Error: {} Details: {}'.format(err, details))
			elif err == 'Timed out Waiting for Volume to be Online':
				raise DriverError(StatusCode.FAILED_PRECONDITION, 'Error: {} Details: {}'.format(err, details))
			else:
				raise DriverError(StatusCode.INVALID_ARGUMENT, err)
		else:
			self.logger.debug(details)

		csiVolume = Volume(volume_id=name, capacity_bytes=capacity)
		return CreateVolumeResponse(volume=csiVolume)

	@CatchServerErrors
	def DeleteVolume(self, request, context):
		Utils.validate_param_exists(request, 'volume_id')

		volume_id = request.volume_id
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(volume_id)
		secrets = request.secrets

		err, out = self.mgmtClient.removeVolume({ '_id': nvmesh_vol_name })
		if err:
			self.logger.error(err)
			raise DriverError(StatusCode.INTERNAL, err)

		self.logger.debug(out)

		if not out['remove'][0]['success']:
			removeResult = out['remove'][0]
			err = removeResult['ex'] if 'ex' in removeResult else 'err'

			if err == "Couldn't find the specified volume":
				pass
			else:
				raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return DeleteVolumeResponse()

	@CatchServerErrors
	def ControllerPublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['node_id', 'volume_id', 'volume_capability'])

		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(request.volume_id)
		self._validate_volume_exists(nvmesh_vol_name)
		self._validate_node_exists(request.node_id)

		err, out = self.mgmtClient.attachVolume(nodeID=request.node_id,volumeID=nvmesh_vol_name)

		if err:
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return ControllerPublishVolumeResponse()

	@CatchServerErrors
	def ControllerUnpublishVolume(self, request, context):
		Utils.validate_params_exists(request, ['node_id', 'volume_id'])

		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(request.volume_id)
		self._validate_volume_exists(nvmesh_vol_name)
		self._validate_node_exists(request.node_id)
		err, out = self.mgmtClient.detachVolume(nodeID=request.node_id,volumeID=nvmesh_vol_name)

		if err:
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return ControllerUnpublishVolumeResponse()

	@CatchServerErrors
	def ValidateVolumeCapabilities(self, request, context):
		Utils.validate_params_exists(request, ['volume_id', 'volume_capabilities'])
		volume_capabilities = request.volume_capabilities
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(request.volume_id)

		volume = self.get_nvmesh_volume(nvmesh_vol_name)

		actual_capabilities = json.loads(volume['description'])['volume_capabilities']
		expected_capabilities = MessageToDict(request)['volumeCapabilities']

		if json.dumps(actual_capabilities) == json.dumps(expected_capabilities):
			confirmed = ValidateVolumeCapabilitiesResponse.Confirmed(volume_capabilities=request.volume_capabilities)
		else:
			confirmed = None
		return ValidateVolumeCapabilitiesResponse(confirmed=confirmed)

	@CatchServerErrors
	def ListVolumes(self, request, context):
		max_entries = request.max_entries
		starting_token = request.starting_token

		try:
			page = int(starting_token or 0)
		except ValueError as ex:
			raise DriverError(StatusCode.ABORTED, "Invalid starting_token")

		get_volumes_kwargs = {
			'projectionObject': { '_id': 1, 'capacity': 1 }
		}

		if starting_token and not max_entries:
			raise DriverError(StatusCode.ABORTED, "Invalid starting_token")

		if max_entries:
			get_volumes_kwargs.update({ 'page': page, 'count': max_entries})

		err, out = self.mgmtClient.getVolumes(**get_volumes_kwargs)
		if err:
			raise DriverError(StatusCode.INTERNAL, err)

		def createEntry(item):
			vol = Volume(volume_id=item['_id'], capacity_bytes=item['capacity'])
			return ListVolumesResponse.Entry(volume=vol)

		entries = map(createEntry, out)
		next_token = str(page + 1)

		if not len(entries):
			DriverError(StatusCode.ABORTED, "No more Entries")

		return ListVolumesResponse(entries=entries, next_token=next_token)

	@CatchServerErrors
	def GetCapacity(self, request, context):
		raise NotImplementedError('Method not implemented!')

	@CatchServerErrors
	def ControllerGetCapabilities(self, request, context):
		def buildCapability(type):
			return ControllerServiceCapability(rpc=ControllerServiceCapability.RPC(type=type))

		create_delete_volume = buildCapability(ControllerServiceCapability.RPC.CREATE_DELETE_VOLUME)
		publish_unpublish = buildCapability(ControllerServiceCapability.RPC.PUBLISH_UNPUBLISH_VOLUME)
		publish_readonly = buildCapability(ControllerServiceCapability.RPC.PUBLISH_READONLY)
		list_volumes = buildCapability(ControllerServiceCapability.RPC.LIST_VOLUMES)
		expand_volume = buildCapability(ControllerServiceCapability.RPC.EXPAND_VOLUME)

		# Not Implemented
		# get_capacity = buildCapability(ControllerServiceCapability.RPC.GET_CAPACITY)
		# create_delete_snapshot = buildCapability(ControllerServiceCapability.RPC.CREATE_DELETE_SNAPSHOT)
		# list_snapshots = buildCapability(ControllerServiceCapability.RPC.LIST_SNAPSHOTS)
		# clone_volume = buildCapability(ControllerServiceCapability.RPC.CLONE_VOLUME)

		capabilities = [
			create_delete_volume,
			publish_unpublish,
			publish_readonly,
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
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(request.volume_id)

		volume = self.get_nvmesh_volume(nvmesh_vol_name)
		capabilities = json.loads(volume['description'])['volume_capabilities']
		capability = capabilities[0]

		# Call Node Expansion Method to Expand a FileSystem
		# For a Block Device there is no need to do anything on the node
		node_expansion_required = True if "mount" in capability else False

		# Extend Volume
		err, out = self.mgmtClient.editVolume({ 'volume': nvmesh_vol_name, 'capacity': capacity_in_bytes})
		if err:
			raise DriverError(StatusCode.NOT_FOUND, err)

		self.logger.debug("ControllerExpandVolumeResponse: capacity_in_bytes={}, node_expansion_required={}".format(capacity_in_bytes, node_expansion_required))
		return ControllerExpandVolumeResponse(capacity_bytes=capacity_in_bytes, node_expansion_required=node_expansion_required)

	def get_nvmesh_volume(self, nvmesh_vol_name):
		projection = {'_id': 1, 'capacity': 1, 'status': 1, 'description': 1}
		err, out = self.mgmtClient.getVolumes(filterObject={'_id': nvmesh_vol_name}, projectionObject=projection, )
		if err:
			raise DriverError(StatusCode.INTERNAL, err)
		if not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Volume {} Could not be found'.format(nvmesh_vol_name))

		return out[0]

	def _parse_raid_type(self, raid_type_string):
		raid_type_string = raid_type_string.lower()

		raid_converter = {
			'lvm': RAIDLevels.CONCATENATED,
			'jbod': RAIDLevels.CONCATENATED,
			'mirrored': RAIDLevels.RAID1,
			'raid1': RAIDLevels.RAID1,
			'raid10': RAIDLevels.RAID10,
			'raid0': RAIDLevels.RAID0,
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
		projection = { '_id': 1, 'capacity': 1 }
		filterObj = { '_id': nvmesh_vol_name }
		err, out = self.mgmtClient.getVolumes(projectionObject=projection, filterObject=filterObj)
		if err or not len(out):
			raise DriverError(StatusCode.INTERNAL, err)

		return out[0]['capacity']

	def _validate_volume_exists(self, nvmesh_vol_name):
		err, out = self.mgmtClient.getVolumes(filterObject={'_id': nvmesh_vol_name}, projectionObject={'_id': 1})
		if err or not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Volume with id {}'.format(nvmesh_vol_name))

	def _validate_node_exists(self, node_id):
		err, out = self.mgmtClient.getServers(filterObject={'node_id': node_id}, projectionObject={ '_id': 1})
		if err or not len(out):
			raise DriverError(StatusCode.NOT_FOUND, 'Could not find Node with id {}'.format(node_id))