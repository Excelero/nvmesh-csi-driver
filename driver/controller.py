from driver.csi.csi_pb2_grpc import ControllerServicer


class NVMeshController(ControllerServicer):
	def CreateVolume(self, request, context):
		pass

	def DeleteVolume(self, request, context):
		pass
