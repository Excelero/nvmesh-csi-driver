import grpc

from driver.csi.csi_pb2 import Volume, CreateVolumeResponse, DeleteVolumeResponse
from driver.csi.csi_pb2_grpc import ControllerServicer
from managementClient import Consts as ManagementClientConsts
from managementClient.ManagementClient import ManagementClient


class NVMeshController(ControllerServicer):
	def __init__(self):
		ControllerServicer.__init__(self)
		self.mgmtClient = ManagementClient()

	def CreateVolume(self, request, context):
		capacity = str(request.capacity_range.required_bytes / 1024) + "K"

		volume = {
			'name': request.name,
			'description': 'created from K8s CSI',
			'RAIDLevel': ManagementClientConsts.RAIDLevels.LVM_JBOD,
			'capacity': capacity
		}
		mgmtResponse = self.mgmtClient.createVolume(volume)[1]
		print(mgmtResponse)

		createResult = mgmtResponse['create'][0]
		if not createResult['success']:
			context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
			context.set_details(createResult['err'])
			return CreateVolumeResponse(volume=volume)
		else:
			# volume created successfully
			volume = self._create_volume_from_mgmt_res(volume['name'], mgmtResponse)
			return CreateVolumeResponse(volume=volume)

	def DeleteVolume(self, request, context):
		print(request)
		mgmtResponse = self.mgmtClient.removeVolume({ 'name': request.name })
		print(mgmtResponse)
		return DeleteVolumeResponse()

	def _create_volume_from_mgmt_res(self, vol_name, mgmtResponse):
		print(mgmtResponse)
		vol = Volume(volume_id=vol_name)
		return vol

def ControllerPublishVolume(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ControllerUnpublishVolume(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ValidateVolumeCapabilities(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ListVolumes(self, request, context):
	raise NotImplementedError('Method not implemented!')

def GetCapacity(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ControllerGetCapabilities(self, request, context):
	raise NotImplementedError('Method not implemented!')

def CreateSnapshot(self, request, context):
	raise NotImplementedError('Method not implemented!')

def DeleteSnapshot(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ListSnapshots(self, request, context):
	raise NotImplementedError('Method not implemented!')

def ControllerExpandVolume(self, request, context):
	raise NotImplementedError('Method not implemented!')