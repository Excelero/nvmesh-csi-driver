import socket

from driver.csi.csi_pb2 import NodeGetInfoResponse, NodeGetCapabilitiesResponse, NodeServiceCapability, NodePublishVolumeResponse, NodeUnpublishVolumeResponse
from driver.csi.csi_pb2_grpc import NodeServicer
from managementClient.ManagementClientWrapper import ManagementClientWrapper


class NVMeshNode(NodeServicer):
	def __init__(self):
		NodeServicer.__init__(self)
		self.mgmtClient = ManagementClientWrapper()

	def NodeStageVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeUnstageVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodePublishVolume(self, request, context):
		volume_id = request.volume_id
		target_path = request.target_path
		staging_target_path = request.staging_target_path
		volume_capability = request.volume_capability
		readonly = request.readonly

		print("NodePublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		# TODO: what should we do here ?
		# should we set the attach path ? (can we ?)
		# should we mount the volume onto the filesystem ?

		return NodePublishVolumeResponse()

	def NodeUnpublishVolume(self, request, context):
		volume_id = request.volume_id
		target_path = request.target_path

		print("NodeUnpublishVolume for volume_id: {} target_path: {}".format(volume_id, target_path))
		# TODO: what should we do here ?
		return NodeUnpublishVolumeResponse()

	def NodeGetVolumeStats(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeExpandVolume(self, request, context):
		raise NotImplementedError('Method not implemented!')

	def NodeGetCapabilities(self, request, context):
		# NodeServiceCapability types
		# enum Type {
		# 		UNKNOWN = 0;
		# 		STAGE_UNSTAGE_VOLUME = 1;
		# 		// If Plugin implements GET_VOLUME_STATS capability
		# 		// then it MUST implement NodeGetVolumeStats RPC
		# 		// call for fetching volume statistics.
		# 		GET_VOLUME_STATS = 2;
		# 		// See VolumeExpansion for details.
		# 		EXPAND_VOLUME = 3;
		#	}
		def buildCapability(type):
			return NodeServiceCapability(rpc=NodeServiceCapability.RPC(type=type))

		get_volume_stats = buildCapability(NodeServiceCapability.RPC.GET_VOLUME_STATS)

		capabilities = []

		return NodeGetCapabilitiesResponse(capabilities=capabilities)

	def NodeGetInfo(self, request, context):
		return NodeGetInfoResponse(node_id=socket.gethostname())

