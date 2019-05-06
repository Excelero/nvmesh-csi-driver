import json
from google.protobuf.json_format import MessageToJson

from driver.common import CatchServerErrors, DriverError, Utils
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
			name = request.name
			capacity = request.capacity_range.required_bytes
			volume_capabilities = request.volume_capabilities
			parameters = request.parameters
			secrets = request.secrets
			volume_content_source = request.volume_content_source
			accessibility_requirements = request.accessibility_requirements

			reqJson = MessageToJson(request)
			self.logger.debug('create volume request: {}'.format(reqJson))

			description_meta_data = {
				'k8s_name': name
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
					raise DriverError(StatusCode.INVALID_ARGUMENT, "Missing raid_level parameter")

				#TODO: should we implement all other parameters ? (i.e stripe_width, num_of_mirrors, EC params.. etc.)

			err, mgmtResponse = self.mgmtClient.createVolume(volume)

			if err:
				raise DriverError(StatusCode.INVALID_ARGUMENT, err)
			else:
				self.logger.debug(mgmtResponse)

			createResult = mgmtResponse['create'][0]
			if not createResult['success']:
				raise DriverError(StatusCode.RESOURCE_EXHAUSTED, createResult['err'])
			else:
				# volume created successfully
				# TODO: Should we wait for the volume to be Online ?
				csiVolume = Volume(volume_id=nvmesh_vol_name, capacity_bytes=capacity)
				return CreateVolumeResponse(volume=csiVolume)

	@CatchServerErrors
	def DeleteVolume(self, request, context):
		volume_id = request.volume_id
		nvmesh_vol_name = Utils.volume_id_to_nvmesh_name(volume_id)
		secrets = request.secrets

		err, out = self.mgmtClient.removeVolume({ '_id': nvmesh_vol_name })
		if err:
			self.logger.error(err)

		self.logger.debug(out)

		if err:
			raise DriverError(StatusCode.INVALID_ARGUMENT, err)

		if not out['remove'][0]['success']:
			removeResult = out['remove'][0]
			err = removeResult['ex'] if 'ex' in removeResult else 'err'
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		# TODO: Should we wait for the volume to be Completely Deleted ?
		return DeleteVolumeResponse()

	@CatchServerErrors
	def ControllerPublishVolume(self, request, context):
		# NVMesh Attach Volume
		err, out = self.mgmtClient.attachVolume(nodeID=request.node_id,volumeID=request.volume_id)

		if err:
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return ControllerPublishVolumeResponse()

	@CatchServerErrors
	def ControllerUnpublishVolume(self, request, context):
		# NVMesh Detach Volume
		err, out = self.mgmtClient.detachVolume(nodeID=request.node_id,volumeID=request.volume_id)

		if err:
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		return ControllerUnpublishVolumeResponse()

	@CatchServerErrors
	def ValidateVolumeCapabilities(self, request, context):
		# TODO: implement Logic to test if the Volume indeed has the following capabilities
		confirmed = ValidateVolumeCapabilitiesResponse.Confirmed(volume_capabilities=request.volume_capabilities)
		return ValidateVolumeCapabilitiesResponse(confirmed=confirmed)

	@CatchServerErrors
	def ListVolumes(self, request, context):
		max_entries = request.max_entries
		starting_token = request.starting_token
		page = int(starting_token or 0)
		projection = {
			'_id': 1,
			'capacity': 1,
			'status': 1
		}

		err, out = self.mgmtClient.getVolumes(page=page, count=max_entries, filterObject=None, sortObject=None, projectionObject=projection)
		if err:
			raise DriverError(StatusCode.FAILED_PRECONDITION, err)

		def createEntry(item):
			vol = Volume(volume_id=item['_id'], capacity_bytes=item['capacity'])
			return ListVolumesResponse.Entry(volume=vol)

		entries = map(createEntry, out)
		next_token = str(page + 1)
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
		list_volumes = buildCapability(ControllerServiceCapability.RPC.LIST_VOLUMES)
		expand_volume = buildCapability(ControllerServiceCapability.RPC.EXPAND_VOLUME)

		capabilities = [
			create_delete_volume,
			publish_unpublish,
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
		editObj = {
			'volume': request.volume_id,
			'capacity': capacity_in_bytes
		}

		err, out = self.mgmtClient.editVolume(editObj)
		if err:
			raise DriverError(StatusCode.NOT_FOUND, err)

		node_expansion_required = False
		return ControllerExpandVolumeResponse(capacity_bytes=capacity_in_bytes, node_expansion_required=node_expansion_required)

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
