import json
import unittest

from grpc._channel import _Rendezvous

from driver.config import Config, print_config
from driver.csi.csi_pb2 import TopologyRequirement, Topology
from driver.topology import RoundRobinZonePicker
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock, DEFAULT_CONFIG_TOPOLOGY, ACTIVE_MANAGEMENT_SERVER
from test.sanity.helpers.setup_and_teardown import start_server

import driver.consts as Consts

from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning
from test.sanity.clients.controller_client import ControllerClient
from test.sanity.helpers.error_handlers import CatchRequestErrors

GB = pow(1024, 3)
VOL_1_ID = "vol_1"
VOL_2_ID = "vol_2"
DEFAULT_TOPOLOGY = Topology(segments={Consts.TopologyKey.ZONE: 'A'})
DEFAULT_TOPOLOGY_REQUIREMENTS = TopologyRequirement(requisite=[DEFAULT_TOPOLOGY], preferred=[DEFAULT_TOPOLOGY])


class TestControllerServiceWithoutTopology(TestCaseWithServerRunning):
	driver_server = None

	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)

	@classmethod
	def setUpClass(cls):
		config = {
			'MANAGEMENT_SERVERS': ACTIVE_MANAGEMENT_SERVER,
			'MANAGEMENT_PROTOCOL': 'https',
			'MANAGEMENT_USERNAME': 'admin@excelero.com',
			'MANAGEMENT_PASSWORD': 'admin',
			'TOPOLOGY_TYPE': None,
			'TOPOLOGY': None,
		}
		ConfigLoaderMock(config).load()
		print_config()
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
	def test_validate_volume_capabilities(self):
		msg = self.ctrl_client.ValidateVolumeCapabilities(volume_id="vol_1")
		print(msg)

	@CatchRequestErrors
	@unittest.skip('ListVolumes need to be updated to use new NVMeshSDK')
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
			#'LIST_VOLUMES',
			'EXPAND_VOLUME',
		}

		self.assertSetEqual(expectedCapabilities, capabilitiesReceived)

	@CatchRequestErrors
	def test_controller_expand_volume(self):
		original_topology_type = Config.TOPOLOGY_TYPE
		Config.TOPOLOGY_TYPE = Consts.TopologyType.SINGLE_ZONE_CLUSTER
		print('TOPOLOGY_TYPE=%s' % Config.TOPOLOGY_TYPE)

		def restoreConfigParams():
			Config.TOPOLOGY_TYPE = original_topology_type

		self.addCleanup(restoreConfigParams)
		original_size = 5*GB
		new_size = 10*GB
		parameters = { 'vpg': 'DEFAULT_CONCATENATED_VPG' }
		print('TOPOLOGY_TYPE=%s' % Config.TOPOLOGY_TYPE)
		msg = self.ctrl_client.CreateVolume(name="vol_to_extend", capacity_in_bytes=original_size, parameters=parameters)
		volume_id = msg.volume.volume_id
		msg = self.ctrl_client.ControllerExpandVolume(volume_id=volume_id, new_capacity_in_bytes=new_size)
		self.ctrl_client.DeleteVolume(volume_id=volume_id)

		self.assertEquals(msg.capacity_bytes, new_size)


class TestControllerServiceWithZoneTopology(TestCaseWithServerRunning):
	driver_server = None
	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)

	@classmethod
	def setUpClass(cls):
		super(TestControllerServiceWithZoneTopology, cls).setUpClass()
		config = {
			'MANAGEMENT_SERVERS': None,
			'MANAGEMENT_PROTOCOL': None,
			'MANAGEMENT_USERNAME': None,
			'MANAGEMENT_PASSWORD': None,
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': DEFAULT_CONFIG_TOPOLOGY
		}

		ConfigLoaderMock(config).load()
		print_config()
		cls.driver_server = start_server(Consts.DriverType.Controller)
		cls.ctrl_client = ControllerClient()

	@classmethod
	def tearDownClass(cls):
		cls.driver_server.stop()

	@CatchRequestErrors
	def test_create_and_delete_volume(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		response = self.ctrl_client.CreateVolume(
			name=VOL_1_ID,
			capacity_in_bytes=5 * GB,
			parameters=parameters,
			topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)

		volume_id = response.volume.volume_id
		self.assertTrue(volume_id)

		accessible_topology = response.volume.accessible_topology
		self.assertTrue(accessible_topology[0].segments.get(Consts.TopologyKey.ZONE), DEFAULT_TOPOLOGY.segments.get(Consts.TopologyKey.ZONE))

		msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
		self.assertTrue(msg)

	@CatchRequestErrors
	def test_create_volume_with_zone_picking(self):
		all_topologies = [
			Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
			Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
			Topology(segments={Consts.TopologyKey.ZONE: 'C'})
		]

		topology_requirements = TopologyRequirement(requisite=all_topologies, preferred=all_topologies)

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		response = self.ctrl_client.CreateVolume(
			name=VOL_1_ID,
			capacity_in_bytes=5 * GB,
			parameters=parameters,
			topology_requirements=topology_requirements)

		volume_id = response.volume.volume_id
		self.assertTrue(volume_id)

		accessible_topology = response.volume.accessible_topology
		print('Got volume with accessible_topology=%s' % accessible_topology)
		got = accessible_topology[0].segments.get(Consts.TopologyKey.ZONE)
		all_options = map(lambda x: x.segments.get(Consts.TopologyKey.ZONE), all_topologies)
		self.assertIn(got, all_options)

		msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
		self.assertTrue(msg)

	@CatchRequestErrors
	def test_fail_if_zone_not_in_topology_config(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		wrong_topology = Topology(segments={Consts.TopologyKey.ZONE: 'wrong_zone'})
		wrong_topology_req = TopologyRequirement(requisite=[wrong_topology], preferred=[wrong_topology])

		try:
			print('Config.TOPOLOGY=%s' % json.dumps(Config.TOPOLOGY, indent=4))
			self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=1 * GB, parameters=parameters, topology_requirements=wrong_topology_req)
			self.fail('Expected ValueError exception')
		except _Rendezvous as ex:
			print(ex)
			self.assertTrue("Zone wrong_zone missing from Config.topology" in ex.details())

	@CatchRequestErrors
	def test_fail_to_create_existing_volume(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		msg = self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=1 * GB, parameters=parameters, topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)

		def delete_volume():
			self.ctrl_client.DeleteVolume(volume_id=msg.volume.volume_id)

		self.addCleanup(delete_volume)

		def createExistingVolume():
			self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=2 * GB, parameters=parameters, topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)

		self.assertRaises(_Rendezvous, createExistingVolume)

	@CatchRequestErrors
	def test_validate_volume_capabilities(self):
		msg = self.ctrl_client.ValidateVolumeCapabilities(volume_id="vol_1")
		print(msg)

	@CatchRequestErrors
	def test_controller_get_capabilities(self):
		msg = self.ctrl_client.GetCapabilities()

		def get_capability_string(cap):
			return str(cap.rpc).split(':')[1].strip()

		capabilitiesReceived = set(map(get_capability_string, msg.capabilities))
		expectedCapabilities = {
			'CREATE_DELETE_VOLUME',
			#'LIST_VOLUMES',
			'EXPAND_VOLUME',
		}

		self.assertSetEqual(expectedCapabilities, capabilitiesReceived)

	@CatchRequestErrors
	def test_controller_expand_volume(self):
		original_size = 5*GB
		new_size = 10*GB
		parameters = { 'vpg': 'DEFAULT_CONCATENATED_VPG' }
		print('TOPOLOGY_TYPE=%s' % Config.TOPOLOGY_TYPE)
		msg = self.ctrl_client.CreateVolume(name="vol_to_extend", capacity_in_bytes=original_size, parameters=parameters, topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)
		volume_id = msg.volume.volume_id
		msg = self.ctrl_client.ControllerExpandVolume(volume_id=volume_id, new_capacity_in_bytes=new_size)
		self.ctrl_client.DeleteVolume(volume_id=volume_id)

		self.assertEquals(msg.capacity_bytes, new_size)

	def test_round_robin_zone_picker(self):
		picker = RoundRobinZonePicker()
		selection_sequence = []

		for i in range(6):
			zone = picker.pick_zone([])
			selection_sequence.append(zone)

		self.assertNotEqual(selection_sequence[0], selection_sequence[1])
		self.assertNotEqual(selection_sequence[1], selection_sequence[2])
		self.assertNotEqual(selection_sequence[0], selection_sequence[2])

		self.assertEqual(selection_sequence[0], selection_sequence[3])
		self.assertEqual(selection_sequence[1], selection_sequence[4])
		self.assertEqual(selection_sequence[2], selection_sequence[5])

if __name__ == '__main__':
	unittest.main()