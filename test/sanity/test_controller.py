import json
import os
import threading
import time
import unittest
from threading import Thread

from grpc import StatusCode
from grpc._channel import _Rendezvous

from driver.config import Config, print_config
from driver.csi.csi_pb2 import TopologyRequirement, Topology
from driver.topology_utils import RoundRobinZonePicker
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock, DEFAULT_CONFIG_TOPOLOGY, ACTIVE_MANAGEMENT_SERVER
from test.sanity.helpers.sanity_test_config import SanityTestConfig
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
TOPO_REQ_MULTIPLE_TOPOLOGIES = TopologyRequirement(
	requisite=[
		Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'C'})
	],
	preferred=[
		Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
		Topology(segments={Consts.TopologyKey.ZONE: 'C'})
	])

os.environ['DEVELOPMENT'] = 'TRUE'

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
			'SDK_LOG_LEVEL': 'DEBUG'
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
		parameters = {
			'vpg': 'DEFAULT_CONCATENATED_VPG',
			'csi.storage.k8s.io/pvc/name': 'some-pvc-name',
			'csi.storage.k8s.io/pv/name': 'pvc-efa59f83-807a-4682-8c95-29ff08cf6b93',
			'csi.storage.k8s.io/pvc/namespace': 'default',
		}
		msg = self.ctrl_client.CreateVolume(name=VOL_1_ID, capacity_in_bytes=5 * GB, parameters=parameters)
		volume_id = msg.volume.volume_id
		self.assertTrue(volume_id)

		msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
		self.assertTrue(msg)

	@CatchRequestErrors
	def test_fail_to_create_volume_not_enough_space(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		ten_tera_byte = 10 * 1000 * GB
		with self.assertRaises(_Rendezvous):
			self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=ten_tera_byte, parameters=parameters)

	@CatchRequestErrors
	def test_fail_to_create_existing_volume(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		msg = self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=1 * GB, parameters=parameters)

		def delete_volume():
			self.ctrl_client.DeleteVolume(volume_id=msg.volume.volume_id)

		self.addCleanup(delete_volume)

		with self.assertRaises(_Rendezvous):
			self.ctrl_client.CreateVolume(name=VOL_2_ID, capacity_in_bytes=2 * GB, parameters=parameters)

	@CatchRequestErrors
	def test_success_create_existing_volume_with_the_same_capacity(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		msg = self.ctrl_client.CreateVolume(name='exists-same-capacity', capacity_in_bytes=1 * GB, parameters=parameters)
		volume_id = msg.volume.volume_id
		self.ctrl_client.CreateVolume(name='exists-same-capacity', capacity_in_bytes=1 * GB, parameters=parameters)
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

		def restoreConfigParams():
			Config.TOPOLOGY_TYPE = original_topology_type

		self.addCleanup(restoreConfigParams)
		original_size = 5*GB
		new_size = 10*GB
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
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
			'TOPOLOGY': DEFAULT_CONFIG_TOPOLOGY,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'DEBUG'
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
	def test_fail_to_create_volume_not_enough_space(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		ten_tera_byte = 10 * 1000 * GB

		with self.assertRaises(_Rendezvous):
			self.ctrl_client.CreateVolume(
				name=VOL_2_ID,
				capacity_in_bytes=ten_tera_byte,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

	@CatchRequestErrors
	def test_create_multiple_volumes(self):
		parameters = {'vpg': 'DEFAULT_RAID_10_VPG'}
		volume_ids = []

		threads = []

		def create_volume(volume_name):
			response = self.ctrl_client.CreateVolume(
				name=volume_name,
				capacity_in_bytes=2 * GB,
				parameters=parameters,
				topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)

			volume_id = response.volume.volume_id
			volume_ids.append(volume_id)
			self.assertTrue(volume_id)

			accessible_topology = response.volume.accessible_topology
			self.assertTrue(accessible_topology[0].segments.get(Consts.TopologyKey.ZONE), DEFAULT_TOPOLOGY.segments.get(Consts.TopologyKey.ZONE))

		def delete_volume(volume_id):
			msg = self.ctrl_client.DeleteVolume(volume_id=volume_id)
			self.assertTrue(msg)

		for i in range(40):
			volume_name = 'vol_%s' % i
			t = Thread(target=create_volume, args=(volume_name,))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()

		print('All create threads finished')

		threads = []
		for volume_id in volume_ids:
			t = Thread(target=delete_volume, args=(volume_id,))
			t.start()
			threads.append(t)

		for t in threads:
			t.join()

	@CatchRequestErrors
	def test_create_volume_with_zone_picking(self):

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		response = self.ctrl_client.CreateVolume(
			name=VOL_1_ID,
			capacity_in_bytes=5 * GB,
			parameters=parameters,
			topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

		volume_id = response.volume.volume_id
		self.assertTrue(volume_id)

		self.addCleanup(lambda: self.ctrl_client.DeleteVolume(volume_id=volume_id))

		accessible_topology = response.volume.accessible_topology
		print('Got volume with accessible_topology=%s' % accessible_topology)
		got = accessible_topology[0].segments.get(Consts.TopologyKey.ZONE)
		all_options = map(lambda x: x.segments.get(Consts.TopologyKey.ZONE), TOPO_REQ_MULTIPLE_TOPOLOGIES.preferred)
		self.assertIn(got, all_options)

	@CatchRequestErrors
	def test_fail_if_zone_not_in_topology_config(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}

		wrong_topology = Topology(segments={Consts.TopologyKey.ZONE: 'wrong_zone'})
		wrong_topology_req = TopologyRequirement(requisite=[wrong_topology], preferred=[wrong_topology])

		try:
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
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		print('TOPOLOGY_TYPE=%s' % Config.TOPOLOGY_TYPE)
		msg = self.ctrl_client.CreateVolume(name="vol_to_extend", capacity_in_bytes=original_size, parameters=parameters, topology_requirements=DEFAULT_TOPOLOGY_REQUIREMENTS)
		volume_id = msg.volume.volume_id
		print(volume_id)
		msg = self.ctrl_client.ControllerExpandVolume(volume_id=volume_id, new_capacity_in_bytes=new_size)
		self.ctrl_client.DeleteVolume(volume_id=volume_id)

		self.assertEquals(msg.capacity_bytes, new_size)

	@CatchRequestErrors
	def test_create_volume_idempotency_sequential(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		def create_volume():
			return self.ctrl_client.CreateVolume(
				name='pvc-test-idempotency-sequential',
				capacity_in_bytes=5 * GB,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

		response1 = create_volume()
		volume_id_1 = response1.volume.volume_id
		self.assertTrue(volume_id_1)

		def delete_volume():
			msg = self.ctrl_client.DeleteVolume(volume_id=volume_id_1)
			self.assertTrue(msg)

		self.addCleanup(delete_volume)

		topology_1 = response1.volume.accessible_topology

		response2 = create_volume()
		volume_id_2 = response2.volume.volume_id
		self.assertEqual(volume_id_1, volume_id_2)

		topology_2 = response2.volume.accessible_topology
		self.assertEqual(topology_1, topology_2)

	@CatchRequestErrors
	def test_create_volume_idempotency_parallel(self):
		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		responses = {}
		lock = threading.Lock()

		def create_volume(index):
			response = self.ctrl_client.CreateVolume(
				name='pvc-test-idempotency-parallel',
				capacity_in_bytes=5 * GB,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

			with lock:
				responses[index] = response

		t1 = threading.Thread(target=create_volume, args=(1,))
		t2 = threading.Thread(target=create_volume, args=(2,))

		t1.start()
		t2.start()

		t1.join()
		t2.join()

		self.ctrl_client.DeleteVolume(volume_id=responses[1].volume.volume_id or responses[2].volume.volume_id)

		self.assertEqual(responses[1].volume.volume_id, responses[2].volume.volume_id)
		self.assertEqual(responses[1].volume.accessible_topology, responses[2].volume.accessible_topology)

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

class TestRetryOnAnotherZone(TestCaseWithServerRunning):
	'''
	Need a whole class as we need to start the server each test so that it will load a specific topology every time
	'''

	def test_retry_on_another_zone(self):
		only_zone_c_active = {
					"zones": {
							"A": {
								"management": {
									"servers": "some-unavailable-server-1:4000"
								}
							},
							"B": {
								"management": {
									"servers": "some-unavailable-server-2:4000"
								}
							},
							"C": {
								"management": {
									"servers": ACTIVE_MANAGEMENT_SERVER
								}
							},
							"D": {
							"management": {
								"servers": "some-unavailable-server-4:4000"
							}
						},
						}
					}

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': only_zone_c_active,
			'LOG_LEVEL':'INFO',
			'SDK_LOG_LEVEL': 'INFO'
		}

		ConfigLoaderMock(config).load()
		driver_server = start_server(Consts.DriverType.Controller)

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		ctrl_client = ControllerClient()
		res = ctrl_client.CreateVolume(
				name=VOL_2_ID,
				capacity_in_bytes=1 * GB,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

		driver_server.stop()

		self.assertTrue(res.volume.volume_id.startswith('C:'))


	@CatchRequestErrors
	def test_fail_to_create_all_mgmts_not_available(self):
		all_inactive = {
			"zones": {
				"A": {
					"management": {"servers": "some-unavailable-server-1:4000"}
				},
				"B": {
					"management": {"servers": "some-unavailable-server-2:4000"}
				},
				"C": {
					"management": {"servers": "some-unavailable-server-3:4000"}
				}
			}
		}

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': all_inactive,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'INFO'
		}

		ConfigLoaderMock(config).load()
		driver_server = start_server(Consts.DriverType.Controller)

		self.addCleanup(lambda: driver_server.stop())

		with self.assertRaises(_Rendezvous):
			parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
			ctrl_client = ControllerClient()
			res = ctrl_client.CreateVolume(
				name=VOL_2_ID,
				capacity_in_bytes=1 * GB,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

	@CatchRequestErrors
	def test_fail_available_zones_not_in_allowed_topology(self):
		all_inactive = {
			"zones": {
				"A": {
					"management": {"servers": "some-unavailable-server-1:4000"}
				},
				"B": {
					"management": {"servers": ACTIVE_MANAGEMENT_SERVER}
				},
				"C": {
					"management": {"servers": "some-unavailable-server-3:4000"}
				}
			}
		}

		requirement = TopologyRequirement(
			requisite=[
				Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
				Topology(segments={Consts.TopologyKey.ZONE: 'C'})
			],
			preferred=[
				Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
				Topology(segments={Consts.TopologyKey.ZONE: 'C'})
			])

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': all_inactive,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'INFO'
		}

		ConfigLoaderMock(config).load()
		driver_server = start_server(Consts.DriverType.Controller)

		self.addCleanup(lambda: driver_server.stop())

		with self.assertRaises(_Rendezvous):
			parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
			ctrl_client = ControllerClient()
			res = ctrl_client.CreateVolume(
				name=VOL_2_ID,
				capacity_in_bytes=1 * GB,
				parameters=parameters,
				topology_requirements=requirement)

	@CatchRequestErrors
	def test_disable_zone_single_allowed_zone(self):
		single_inactive = {
			"zones": {
				"A": {
					"management": {"servers": "some-unavailable-server-1:4000"}
				}
			}
		}

		single_zone = [Topology(segments={Consts.TopologyKey.ZONE: 'A'})]
		requirement = TopologyRequirement(requisite=single_zone, preferred=single_zone)

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': single_inactive,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'INFO'
		}

		ConfigLoaderMock(config).load()
		driver_server = start_server(Consts.DriverType.Controller)

		self.addCleanup(lambda: driver_server.stop())

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		ctrl_client = ControllerClient()

		def assert_fail_to_create_volume(volume_id):

			try:
				res = ctrl_client.CreateVolume(
					name=volume_id,
					capacity_in_bytes=1 * GB,
					parameters=parameters,
					topology_requirements=requirement)

				self.addCleanup(lambda: ctrl_client.DeleteVolume(volume_id=res.volume_id))
			except _Rendezvous as ex:
				self.assertEquals(ex._state.code, StatusCode.RESOURCE_EXHAUSTED)
				self.assertIn('Failed to create volume on all zones', ex.debug_error_string())

		assert_fail_to_create_volume(VOL_1_ID)
		assert_fail_to_create_volume(VOL_2_ID)

	@CatchRequestErrors
	def test_disable_zone_multiple_allowed_zone(self):
		single_inactive = {
			"zones": {
				"A": {
					"management": {"servers": "some-unavailable-server-1:4000"}
				},
				"B": {
					"management": {"servers": "some-unavailable-server-2:4000"}
				},
				"C": {
					"management": {"servers": "some-unavailable-server-3:4000"}
				}
			}
		}

		full_topology = [
			Topology(segments={Consts.TopologyKey.ZONE: 'A'}),
			Topology(segments={Consts.TopologyKey.ZONE: 'B'}),
			Topology(segments={Consts.TopologyKey.ZONE: 'C'})
		]
		requirement = TopologyRequirement(requisite=full_topology, preferred=full_topology)

		config = {
			'TOPOLOGY_TYPE': Consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'TOPOLOGY': single_inactive,
			'LOG_LEVEL': 'DEBUG',
			'SDK_LOG_LEVEL': 'INFO'
		}

		ConfigLoaderMock(config).load()
		driver_server = start_server(Consts.DriverType.Controller)

		self.addCleanup(lambda: driver_server.stop())

		parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
		ctrl_client = ControllerClient()

		def assert_fail_to_create_volume(volume_id):
			try:
				res = ctrl_client.CreateVolume(
					name=volume_id,
					capacity_in_bytes=1 * GB,
					parameters=parameters,
					topology_requirements=requirement)

				self.addCleanup(lambda: ctrl_client.DeleteVolume(volume_id=res.volume_id))
			except _Rendezvous as ex:
				self.assertEquals(ex._state.code, StatusCode.RESOURCE_EXHAUSTED)
				self.assertIn('Failed to create volume on all zones', ex.debug_error_string())

		assert_fail_to_create_volume(VOL_1_ID)
		assert_fail_to_create_volume(VOL_2_ID)



class TestServerShutdown(TestCaseWithServerRunning):
	'''
	These are test cases to check that while the server terminates all running requests are able to finish successfully
	'''
	def test_abort_during_request(self):
		config = {
			'MANAGEMENT_SERVERS': SanityTestConfig.ManagementServers[0],
			'MANAGEMENT_PROTOCOL': 'https',
			'MANAGEMENT_USERNAME': 'admin@excelero.com',
			'MANAGEMENT_PASSWORD': 'admin',
			'TOPOLOGY_TYPE': Consts.TopologyType.SINGLE_ZONE_CLUSTER,
			'TOPOLOGY': None
		}

		ConfigLoaderMock(config).load()

		driver_server = start_server(Consts.DriverType.Controller)
		response_bucket = []

		def create_volume(response_bucket):
			ctrl_client = ControllerClient()
			parameters = {'vpg': 'DEFAULT_CONCATENATED_VPG'}
			res = ctrl_client.CreateVolume(
				name='pvc-test-graceful-shutdown',
				capacity_in_bytes=5 * GB,
				parameters=parameters,
				topology_requirements=TOPO_REQ_MULTIPLE_TOPOLOGIES)

			print('create_volume returned %s' % res)
			response_bucket.append(res.volume.volume_id)

		t = threading.Thread(target=create_volume, args=(response_bucket,))
		t.start()
		time.sleep(2)
		driver_server.stop()

		# if volume_id is None that means the thread pre-maturely terminated
		self.assertTrue(response_bucket[0])

if __name__ == '__main__':
	unittest.main()