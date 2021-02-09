import time
import unittest

from grpc._channel import _Rendezvous

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.MongoObj import MongoObj
from driver.csi.csi_pb2 import TopologyRequirement, Topology
from test.sanity.helpers.setup_and_teardown import start_server

import driver.consts as Consts

from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning
from test.sanity.clients.controller_client import ControllerClient
from test.sanity.helpers.error_handlers import CatchRequestErrors

GB = pow(1024, 3)
VOL_1_ID = "vol_1"
VOL_2_ID = "vol_2"
NODE_ID = "nvme117.excelero.com"

class TestControllerService(TestCaseWithServerRunning):
	driver_server = None

	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)

	@classmethod
	def setUpClass(cls):
		super(TestControllerService, cls).setUpClass()
		cls.driver_server = start_server(Consts.DriverType.Controller)
		cls.ctrl_client = ControllerClient()

	@classmethod
	def tearDownClass(cls):
		cls.driver_server.stop()

	@CatchRequestErrors
	def test_create_and_delete_volume(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		msg = self.ctrl_client.CreateVolume(name=VOL_1_ID, capacity_in_bytes=5 * GB, parameters=parameters)
		volume_id = msg.volume.volume_id
		self.assertTrue(volume_id)

		msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
		self.assertTrue(msg)

	@CatchRequestErrors
	def test_fail_to_create_existing_volume(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		msg = self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=1 * GB, parameters=parameters)

		def delete_volume():
			self.ctrl_client.DeleteVolume(volume_id=msg.volume.volume_id)

		self.addCleanup(delete_volume)

		def createExistingVolume():
			self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=2 * GB, parameters=parameters)

		self.assertRaises(_Rendezvous, createExistingVolume)

	@CatchRequestErrors
	def test_success_create_existing_volume_with_the_same_capacity(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		msg = self.ctrl_client.CreateVolume(name=VOL_1_ID, capacity_in_bytes=1 * GB, parameters=parameters)
		volume_id = msg.volume.volume_id
		self.ctrl_client.CreateVolume(name=VOL_1_ID, capacity_in_bytes=1 * GB, parameters=parameters)
		self.ctrl_client.DeleteVolume(volume_id=volume_id)

	@CatchRequestErrors
	def test_create_volume_with_topology(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		topology_requirements = TopologyRequirement(requisite=[Topology(segments={'key':'value'})])
		msg = self.ctrl_client.CreateVolume(
			name=VOL_1_ID,
			capacity_in_bytes=5 * GB,
			parameters=parameters,
			topology_requirements=topology_requirements)

		volume_id = msg.volume.volume_id
		self.assertTrue(volume_id)

		msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
		self.assertTrue(msg)

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

		def get_capability_string(cap):
			return str(cap.rpc).split(':')[1].strip()

		capabilitiesReceived = set(map(get_capability_string, msg.capabilities))
		expectedCapabilities = {
			'CREATE_DELETE_VOLUME',
			'LIST_VOLUMES',
			'EXPAND_VOLUME',
		}

		self.assertSetEqual(expectedCapabilities, capabilitiesReceived)

	@CatchRequestErrors
	def test_controller_expand_volume(self):
		original_size = 5*GB
		new_size = 10*GB
		parameters = { 'vpg': 'DEFAULT_CONCATENATED_VPG' }
		msg = self.ctrl_client.CreateVolume(name="vol_to_extend", capacity_in_bytes=original_size, parameters=parameters)
		volume_id = msg.volume.volume_id
		msg = self.ctrl_client.ControllerExpandVolume(volume_id=volume_id, new_capacity_in_bytes=new_size)
		self.ctrl_client.DeleteVolume(volume_id=volume_id)

		self.assertEquals(msg.capacity_bytes, new_size)

if __name__ == '__main__':
	unittest.main()