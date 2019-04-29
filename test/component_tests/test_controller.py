import unittest


from test.clients.controller_client import ControllerClient
from test.helpers.error_handlers import CatchRequestErrors
from test.helpers.test_case_with_server import TestCaseWithServerRunning

GB = 1024*1024*1024
VOL_ID="vol_1"
VOL_FOR_EXTENSION="vol_to_extend"
NODE_ID="Gil-Laptop"

class TestControllerService(TestCaseWithServerRunning):
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)
		self.ctrl_client = ControllerClient()

	@CatchRequestErrors
	def test_create_volume(self):
		msg = self.ctrl_client.CreateVolume(name=VOL_ID, capacity_in_bytes=5*GB)
		self.assertEquals(msg.volume.volume_id, VOL_ID)

	@CatchRequestErrors
	def test_publish_volume(self):
		msg = self.ctrl_client.PublishVolume(volume_id=VOL_ID, node_id=NODE_ID)
		print(msg)

	@CatchRequestErrors
	def test_unpublish_volume(self):
		msg = self.ctrl_client.UnpublishVolume(volume_id="vol_1", node_id=NODE_ID)
		print(msg)

	@CatchRequestErrors
	def test_validate_volume_capabilities(self):
		msg = self.ctrl_client.ValidateVolumeCapabilities(volume_id="vol_1")
		print(msg)

	@CatchRequestErrors
	def test_list_volumes(self):
		msg = self.ctrl_client.ListVolumes(max_entries=2)
		print(msg.entries)
		msg = self.ctrl_client.ListVolumes(max_entries=2, starting_token=msg.next_token)
		print(msg.entries)

	@CatchRequestErrors
	def test_controller_get_capabilities(self):
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

	@CatchRequestErrors
	def test_controller_expand_volume(self):
		original_size = 5*GB
		new_size = 10*GB
		self.ctrl_client.CreateVolume(name=VOL_FOR_EXTENSION, capacity_in_bytes=original_size)
		msg = self.ctrl_client.ControllerExpandVolume(volume_id=VOL_FOR_EXTENSION, new_capacity_in_bytes=new_size)
		self.ctrl_client.DeleteVolume(volume_id=VOL_FOR_EXTENSION)

		self.assertEquals(msg.capacity_bytes, new_size)

	@CatchRequestErrors
	def test_delete_volume(self):
		msg = self.ctrl_client.DeleteVolume(volume_id=VOL_ID)
		print(msg)

if __name__ == '__main__':
	unittest.main()