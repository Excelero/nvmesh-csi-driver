import socket

from driver.csi.csi_pb2 import NodeGetInfoResponse
from driver.csi.csi_pb2_grpc import NodeServicer
from managementClient.ManagementClient import ManagementClient


class NVMeshNode(NodeServicer):
	def __init__(self):
		NodeServicer.__init__(self)
		self.mgmtClient = ManagementClient()

	def NodeStageVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeUnstageVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodePublishVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeUnpublishVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeGetVolumeStats(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeExpandVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeGetCapabilities(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeGetInfo(self, request, context):
		return NodeGetInfoResponse(node_id=socket.gethostname())

