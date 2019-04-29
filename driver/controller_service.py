import grpc

from driver.common import CatchServerErrors
from driver.csi.csi_pb2 import Volume, CreateVolumeResponse, DeleteVolumeResponse, ControllerPublishVolumeResponse, ControllerUnpublishVolumeResponse, \
	ValidateVolumeCapabilitiesResponse, ListVolumesResponse, ControllerGetCapabilitiesResponse, ControllerServiceCapability, ControllerExpandVolumeResponse
from driver.csi.csi_pb2_grpc import ControllerServicer
from managementClient import Consts as ManagementClientConsts
from managementClient.ManagementClientWrapper import ManagementClientWrapper


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

			volume = {
				'name': name,
				'description': 'created from K8s CSI',
				'RAIDLevel': ManagementClientConsts.RAIDLevels.CONCATENATED,
				'capacity': capacity
			}
			err, mgmtResponse = self.mgmtClient.createVolume(volume)
			self.logger.debug(mgmtResponse)

			createResult = mgmtResponse['create'][0]

			if not createResult['success']:
				context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
				context.set_details(createResult['err'])
				return None
			else:
				# volume created successfully
				csiVolume = self._create_volume_from_mgmt_res(volume['name'])
				return CreateVolumeResponse(volume=csiVolume)

	@CatchServerErrors
	def DeleteVolume(self, request, context):
		volume_id = request.volume_id
		secrets = request.secrets

		err, out = self.mgmtClient.removeVolume({ '_id': request.volume_id })
		if err:
			self.logger.error(err)

		self.logger.debug(out)

		if err:
			context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
			context.set_details(str(err))
		else:

			if not out['remove'][0]['success']:
				removeResult = out['remove'][0]
				err = removeResult['ex'] if 'ex' in removeResult else 'err'
				context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
				context.set_details(err)

		return DeleteVolumeResponse()

	def _create_volume_from_mgmt_res(self, vol_name):
		vol = Volume(volume_id=vol_name)
		return vol

	@CatchServerErrors
	def ControllerPublishVolume(self, request, context):
		# NVMesh Attach Volume
		err, out = self.mgmtClient.attachVolume(nodeID=request.node_id,volumeID=request.volume_id)

		if err:
			context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
			context.set_details(err)

		return ControllerPublishVolumeResponse()

	@CatchServerErrors
	def ControllerUnpublishVolume(self, request, context):
		# NVMesh Detach Volume
		err, out = self.mgmtClient.detachVolume(nodeID=request.node_id,volumeID=request.volume_id)

		if err:
			context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
			context.set_details(err)

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
			context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
			context.set_details(err)

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
			context.set_code(grpc.StatusCode.NOT_FOUND)
			context.set_details(err)

		node_expansion_required = False
		return ControllerExpandVolumeResponse(capacity_bytes=capacity_in_bytes, node_expansion_required=node_expansion_required)