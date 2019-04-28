import unittest

from grpc import StatusCode
from grpc._channel import _Rendezvous

from test.clients.controller_client import ControllerClient
from test.helpers.test_case_with_server import TestCaseWithServerRunning

GB = 1024*1024*1024
VOL_ID="vol_1"
NODE_ID="Gil-Laptop"

def handleGRPCError(action, grpcError):
	if grpcError._state.code == StatusCode.FAILED_PRECONDITION:
		print('{action} failed with code {code} details: {details}'.format(
			action=action,
			code=grpcError._state.code,
			details=grpcError._state.details))
	else:
		raise(grpcError)

class CatchRequestErrors(object):
	def __init__(self, action_name):
		self.action_name = action_name

	def __enter__(self):
		pass

	def __exit__(self, type, value, traceback):
		if type == _Rendezvous:
			handleGRPCError(self.action_name, value)

class TestControllerService(TestCaseWithServerRunning):
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self.ctrl_client = ControllerClient()

	def test_create_volume(self):
		with CatchRequestErrors('CreateVolume'):
			msg = self.ctrl_client.CreateVolume(name=VOL_ID, capacity_in_bytes=5*GB)

	def test_delete_volume(self):
		with CatchRequestErrors('DeleteVolume'):
			msg = self.ctrl_client.DeleteVolume(volume_id=VOL_ID)
			print(msg)

	def test_publish_volume(self):
		with CatchRequestErrors('PublishVolume'):
			msg = self.ctrl_client.PublishVolume(volume_id=VOL_ID, node_id=NODE_ID)
			print(msg)

	def test_unpublish_volume(self):
		with CatchRequestErrors('UnpublishVolume'):
			msg = self.ctrl_client.UnpublishVolume(volume_id="vol_1", node_id=NODE_ID)
			print(msg)

	def test_validate_volume_capabilities(self):
		with CatchRequestErrors('ValidateVolumeCapabilities'):
			msg = self.ctrl_client.ValidateVolumeCapabilities(volume_id="vol_1")
			print(msg)

	def test_list_volumes(self):
		with CatchRequestErrors('ListVolumes'):
			msg = self.ctrl_client.ListVolumes(max_entries=2)
			print(msg.entries)
			msg = self.ctrl_client.ListVolumes(max_entries=2, starting_token=msg.next_token)
			print(msg.entries)

	def test_controller_get_capabilities(self):
		with CatchRequestErrors('GetCapabilities'):
			msg = self.ctrl_client.GetCapabilities()

			self.assertEquals(len(msg.capabilities), 4)

			def get_capability_string(cap):
				return str(cap.rpc).split(':')[1].strip()

			capabilitiesReceived = map(get_capability_string, msg.capabilities)
			expectedCapabilities = [
				'CREATE_DELETE_VOLUME',
				'PUBLISH_UNPUBLISH_VOLUME',
				'LIST_VOLUMES',
				'EXPAND_VOLUME',
			]
			self.assertListEqual(expectedCapabilities, capabilitiesReceived)

	def test_controller_expand_volume(self):
		with CatchRequestErrors('ControllerExpandVolume'):
			msg = self.ctrl_client.ControllerExpandVolume(volume_id=VOL_ID, new_capacity_in_bytes=10*GB)
			print(msg)

if __name__ == '__main__':
	unittest.main()