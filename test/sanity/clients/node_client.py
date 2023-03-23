import driver.consts as Consts
from driver.csi.csi_pb2 import NodeGetInfoRequest, NodeGetCapabilitiesRequest, NodeGetVolumeStatsRequest, NodePublishVolumeRequest, VolumeCapability, NodeUnpublishVolumeRequest, \
	NodeStageVolumeRequest, NodeUnstageVolumeRequest, NodeExpandVolumeRequest
from driver.csi.csi_pb2_grpc import NodeStub
from test.sanity.clients.base_client import BaseClient

STAGING_PATH_TEMPLATE = '/var/lib/kubelet/plugins/kubernetes.io/csi/pv/{volume_id}/globalmount'
TARGET_PATH_PARENT_DIR_TEMPLATE = '/var/lib/kubelet/pods/{pod_id}/volumes/kubernetes.io~csi/{volume_id}'
TARGET_PATH_TEMPLATE = '/var/lib/kubelet/pods/{pod_id}/volumes/kubernetes.io~csi/{volume_id}/mount'

class NodeClient(BaseClient):

	def __init__(self):
		# type: () -> NodeClient
		BaseClient.__init__(self)
		self.client = NodeStub(self.intercepted_channel)

	def _build_capability(self, access_type, access_mode, fs_type):
		access_mode_obj = VolumeCapability.AccessMode(mode=access_mode)
		if access_type == Consts.VolumeAccessType.MOUNT:
			mount_req = VolumeCapability.MountVolume(fs_type=fs_type)
			volume_capability = VolumeCapability(mount=mount_req, access_mode=access_mode_obj)
		else:
			volume_capability = VolumeCapability(block=VolumeCapability.BlockVolume(),access_mode=access_mode_obj)

		return volume_capability

	def NodeStageVolume(self, volume_id, access_type=Consts.VolumeAccessType.MOUNT, access_mode=VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER, volume_context=None):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=volume_id)

		volume_capability = self._build_capability(access_type, access_mode, fs_type='ext4')

		req = NodeStageVolumeRequest(
			volume_id=volume_id,
			staging_target_path=staging_target_path,
			volume_capability=volume_capability,
			volume_context=volume_context
		)
		return self.client.NodeStageVolume(req)

	def NodeUnstageVolume(self, volume_id):
		staging_target_path = '/stage/{}'.format(volume_id)
		req = NodeUnstageVolumeRequest(volume_id=volume_id, staging_target_path=staging_target_path)
		return self.client.NodeUnstageVolume(req)

	def NodePublishVolume(self, volume_id, target_path, readonly=False, access_type=Consts.VolumeAccessType.MOUNT, access_mode=VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=volume_id)
		volume_capability = self._build_capability(access_type, access_mode, fs_type='ext4')

		req = NodePublishVolumeRequest(
			volume_id=volume_id,
			staging_target_path=staging_target_path,
			target_path=target_path,
			volume_capability=volume_capability,
			readonly=readonly
		)
		return self.client.NodePublishVolume(req)

	def NodeUnpublishVolume(self, volume_id, target_path):
		req = NodeUnpublishVolumeRequest(volume_id=volume_id, target_path=target_path)
		return self.client.NodeUnpublishVolume(req)

	def NodeGetVolumeStats(self, volume_id, volume_path, staging_target_path):
		req = NodeGetVolumeStatsRequest(
			volume_id=volume_id, 
			volume_path=volume_path, 
			staging_target_path=staging_target_path
		)
		return self.client.NodeGetVolumeStats(req)

	def NodeExpandVolume(self, volume_id, volume_path='some_path'):
		req = NodeExpandVolumeRequest(volume_id=volume_id, volume_path=volume_path)
		return self.client.NodeExpandVolume(req)

	def NodeGetCapabilities(self):
		return self.client.NodeGetCapabilities(NodeGetCapabilitiesRequest())

	def NodeGetInfo(self):
		return self.client.NodeGetInfo(NodeGetInfoRequest())
