import json
import logging
import os
import time
import unittest
from threading import Thread

from grpc import StatusCode
from grpc._channel import _Rendezvous

import driver.consts as Consts
from driver import consts

from driver.csi.csi_pb2 import NodeGetVolumeStatsResponse, NodeServiceCapability, Topology, VolumeCapability, NodePublishVolumeRequest
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.quick_json_schema import JSONSchemaBuilder
from test.sanity.helpers.setup_and_teardown import start_containerized_server
from test.sanity.helpers.test_case_with_server import TestCaseWithServerRunning

from test.sanity.clients.node_client import NodeClient, STAGING_PATH_TEMPLATE, TARGET_PATH_PARENT_DIR_TEMPLATE
from test.sanity.helpers.error_handlers import CatchRequestErrors, CatchNodeDriverErrors
from test.sanity.nvmesh_cluster_simulator.nvmesh_mgmt_sim import NVMeshManagementSim

GB = pow(1024, 3)
VOL_ID = "vol_1"
NODE_ID_1 = "node-1"
DEFAULT_POD_ID = "pod-ab12"
TOPOLOGY_SINGLE_ZONE = {'zones': {'zone_1': {'management': {'servers': 'localhost:4000'}}}}
TOPOLOGY_MULTIPLE_ZONES = Topology(segments={Consts.TopologyKey.ZONE: 'zone_1'})
config_for_driver = None

os.environ['DEVELOPMENT'] = 'TRUE'
log = logging.getLogger('SanityTests')

class TestNodeService(TestCaseWithServerRunning):
	driver_server = None  # ContainerizedCSIDriver: None
	cluster1 = None  # type: NVMeshManagementSim

	def __init__(self, *args, **kwargs):
		TestCaseWithServerRunning.__init__(self, *args, **kwargs)

	@staticmethod
	def restart_server(new_config=None):
		TestNodeService.driver_server.stop()

		config = new_config or TestNodeService.driver_server.config
		ConfigLoaderMock(config).load()
		TestNodeService.driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')

	@classmethod
	def setUpClass(cls):
		log.debug('setUpClass')
		super(TestNodeService, cls).setUpClass()

		# Start Management Simulator
		cls.cluster1 = NVMeshManagementSim('cluster-1')
		cls.cluster1.start()
		log.debug('wait_until_is_alive()')
		cls.cluster1.wait_until_is_alive()
		log.debug('after wait_until_is_alive()')

		cls.cluster1.add_clients({'node-1': {}, 'node-2': {}})

		topology = {
				'type': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
				'zones': {'zone_1': {'management': {'servers': cls.cluster1.get_mgmt_server_string()}}}
			}

		config_for_test = {
			'TOPOLOGY': topology,
		}

		global config_for_driver

		config_for_driver = {
			'topology': json.dumps(topology),
			'sdkLogLevel': 'DEBUG',
			'printStackTraces': 'true',
			'attachIOEnabledTimeout': '3',
		}

		ConfigLoaderMock(config_for_test).load()

		cls.driver_server = start_containerized_server(Consts.DriverType.Node, config=config_for_driver, hostname='node-1')
		config_for_test['SOCKET_PATH'] = 'unix://%s' % cls.driver_server.csi_socket_path

		ConfigLoaderMock(config_for_test).load()
		cls._client = NodeClient()

	@classmethod
	def tearDownClass(cls):
		log.debug('stopping server')
		# To keep the container running after a test comment the following line:
		cls.driver_server.stop()
		log.debug('server stopped')

		log.debug('stopping NVMesh cluster')
		cls.cluster1.stop()
		log.debug('NVMesh cluster stopped')

	@CatchRequestErrors
	def test_get_info_basic_test(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, NODE_ID_1)

	@CatchNodeDriverErrors(NODE_ID_1)
	def test_get_info_with_topology(self):
		res = self._client.NodeGetInfo()
		self.assertEquals(res.node_id, NODE_ID_1)

		topology_info = res.accessible_topology.segments
		log.debug(topology_info)
		# This is configured in ConfigLoaderMock.TOPOLOGY
		self.assertEquals(topology_info.get(Consts.TopologyKey.ZONE), 'zone_1')

	@CatchRequestErrors
	def test_get_info_node_not_found_in_any_mgmt(self):
		self.restart_server()
		TestNodeService.driver_server.set_topology_config_map(json.dumps({}))

		result_bucket = {}
		def do_request(result_bucket):
			res = self._client.NodeGetInfo()
			result_bucket['res'] = res

		time.sleep(2)

		t = Thread(target=do_request, args=(result_bucket,))
		t.start()

		# Make sure the response does not return
		attempts = 5
		while attempts:
			t.join(timeout=1)
			self.assertTrue(t.isAlive())
			attempts = attempts - 1

		zones_dict = {'zoneA': {'nodes': [NODE_ID_1]}}
		TestNodeService.driver_server.set_topology_config_map(json.dumps(zones_dict))
		t.join(timeout=8)
		result = result_bucket.get('res')
		self.assertTrue(result)
		self.assertEquals(result.node_id, NODE_ID_1)

	@CatchRequestErrors
	def test_get_capabilities(self):
		res = self._client.NodeGetCapabilities()
		expected = [NodeServiceCapability.RPC.GET_VOLUME_STATS, NodeServiceCapability.RPC.STAGE_UNSTAGE_VOLUME, NodeServiceCapability.RPC.EXPAND_VOLUME]
		self.assertListEqual(expected, [item.rpc.type for item in list(res.capabilities)])

	@CatchRequestErrors
	def test_get_volume_stats_inexistant_path(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/test-mount'
		
		def do_request():
			return self._client.NodeGetVolumeStats(volume_id=VOL_ID, volume_path=target_path, staging_target_path=staging_target_path)

		self.assertReturnsGrpcError(do_request, StatusCode.INVALID_ARGUMENT, "Volume path does not exist")
	
	@CatchRequestErrors
	def test_get_volume_stats_unmounted(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/test-mount'

		TestNodeService.driver_server.make_dir_in_env_dir(target_path)

		def do_request():
			return self._client.NodeGetVolumeStats(volume_id=VOL_ID, volume_path=target_path, staging_target_path=staging_target_path)

		self.assertReturnsGrpcError(do_request, StatusCode.NOT_FOUND, "Volume path is not mounted")
	
	@CatchRequestErrors
	def test_get_volume_stats_mounted(self):
		nvmesh_attach_script_content = NVMeshAttachScriptMockBuilder().getDefaultSuccessBehavior()
		TestNodeService.driver_server.set_nvmesh_attach_volumes_content(nvmesh_attach_script_content)
		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/test-mount'

		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_path)
		self._client.NodeStageVolume(volume_id=VOL_ID)
		self._client.NodePublishVolume(
			volume_id=VOL_ID,
			target_path=target_path,
			access_type=Consts.VolumeAccessType.MOUNT,
			access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		self.addCleanup(lambda: self._client.NodeUnpublishVolume(VOL_ID, target_path))
		
		_r = self._client.NodeGetVolumeStats(volume_id=VOL_ID, volume_path=target_path, staging_target_path=staging_target_path)

		self.assertIsInstance(_r, NodeGetVolumeStatsResponse)
	
	@CatchRequestErrors
	def test_node_stage_volume_successful(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		self._client.NodeStageVolume(volume_id=VOL_ID)
		log.debug("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_node_stage_mkfs_options(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		volume_context = {
			'mkfsOptions': '-O encrypt'
		}

		self._client.NodeStageVolume(volume_id=VOL_ID, volume_context=volume_context)
		log.debug("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_cleanup_detach_after_timeout_waiting_for_io_enabled(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)

		self.cluster1.update_options({'volumeStatusProcContent': {'dbg': '0x300'}})

		try:
			self._client.NodeStageVolume(volume_id=VOL_ID)
		except _Rendezvous as ex:
			self.assertIn('Timed-out after waiting', str(ex))
			self.assertIn('to have IO Enabled', str(ex))

		attached_device_path = os.path.join(TestNodeService.driver_server.env_dir, 'dev/nvmesh/%s' % VOL_ID)
		is_attached = os.path.exists(attached_device_path)
		self.assertFalse(is_attached)

		log.debug("NodeStageVolume Finished")

	def _test_nvmesh_attach_volume_response(self, status_and_error, expected_code, expected_string_in_details):
		# TODO: tell management sim to return error
		pass

		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		try:
			r = self._client.NodeStageVolume(volume_id=VOL_ID)
			self.assertTrue(False)
		except _Rendezvous as grpcError:
			self.assertEquals(expected_code, grpcError._state.code)
			self.assertIn(expected_string_in_details, grpcError._state.details)

	@CatchRequestErrors
	def test_attach_should_use_preempt_when_flag_is_set_and_mode_rwo(self):
		schema_builder = JSONSchemaBuilder()
		schema_builder.validate_obj_value('volumes[].reservation.preempt', {'enum': [True]})
		schema = schema_builder.get_schema()
		self.cluster1.update_options({'schemas': {'/clients/attach': schema}})

		config_for_driver['usePreempt'] = 'True'
		self.restart_server(new_config=config_for_driver)

		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		r = self._client.NodeStageVolume(volume_id=VOL_ID, access_type=Consts.VolumeAccessType.MOUNT, access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		log.debug("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_attach_should_not_use_preempt_when_flag_is_set_but_mode_is_not_rwo(self):
		schema_builder = JSONSchemaBuilder()
		schema_builder.validate_obj_value('volumes[].reservation.preempt', {'enum': [False]})
		schema = schema_builder.get_schema()
		self.cluster1.update_options({'schemas' : { '/clients/attach': schema }})

		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		r = self._client.NodeStageVolume(volume_id=VOL_ID, access_type=Consts.VolumeAccessType.MOUNT,
										 access_mode=VolumeCapability.AccessMode.MULTI_NODE_READER_ONLY)
		log.debug("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_attach_should_not_use_preempt_when_flag_is_not_set(self):
		schema_builder = JSONSchemaBuilder()
		schema_builder.validate_obj_value('volumes[].reservation.preempt', {'enum': [False]})
		schema = schema_builder.get_schema()
		self.cluster1.update_options({'schemas': {'/clients/attach': schema}})
		try:
			TestNodeService.driver_server.remove_nvmesh_device(VOL_ID)
		except:
			pass

		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		r = self._client.NodeStageVolume(volume_id=VOL_ID, access_type=Consts.VolumeAccessType.MOUNT, access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		log.debug("NodeStageVolume Finished")

	@CatchRequestErrors
	def test_detach_retries_when_volume_is_busy(self):
		# TODO: make mgmt sim return busy
		pass
		new_config = TestNodeService.driver_server.config.copy()
		new_config['attachIOEnabledTimeout'] = '3'
		self.restart_server(new_config=new_config)

		pass
		TestNodeService.driver_server.set_nvmesh_detach_volumes_content()

		try:
			r = self._client.NodeUnstageVolume(volume_id=VOL_ID)
		except _Rendezvous as ex:
			self.assertIn('nvmesh_detach_volumes failed after', str(ex))

		log.debug("NodeUnstageVolume Finished")

	@CatchRequestErrors
	def test_stage_volume_failed_access_mode_denied_workaround(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Attached IO Enabled", "error": "Access Mode Denied."}',
			expected_code=StatusCode.FAILED_PRECONDITION,
			expected_string_in_details='Access Mode Denied'
		)

	@CatchRequestErrors
	def test_stage_volume_failed_reservation_mode_denied(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Attached IO Enabled", "error": "Reservation Mode Denied."}',
			expected_code=StatusCode.FAILED_PRECONDITION,
			expected_string_in_details='Access Mode Denied'
		)

	@CatchRequestErrors
	def test_stage_volume_failed_reservation_mode_denied(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Access Mode Denied"}',
			expected_code=StatusCode.FAILED_PRECONDITION,
			expected_string_in_details='Access Mode Denied'
		)

	@CatchRequestErrors
	def test_stage_volume_failed_access_version_outdated(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Access Version Outdated"}',
			expected_code=StatusCode.INTERNAL,
			expected_string_in_details='Access Version Outdated'
		)

	@CatchRequestErrors
	def test_stage_volume_failed_access_version_outdated(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Attach Failed"}',
			expected_code=StatusCode.INTERNAL,
			expected_string_in_details='Attach Failed'
		)

	@CatchRequestErrors
	def test_stage_volume_failed_access_version_outdated(self):
		self._test_nvmesh_attach_volume_response(
			status_and_error='{"status": "Update Failed", "error": "Volume attach request failed. Failed to update volume. ErrorID: 1047, review system logs for more information."}',
			expected_code=StatusCode.INTERNAL,
			expected_string_in_details='Attach Failed'
		)

	@CatchRequestErrors
	def test_node_publish_volume_fs(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/mount'

		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_parent_dir)
		self._client.NodePublishVolume(
			volume_id=VOL_ID,
			target_path=target_parent_dir + '/mount',
			access_type=Consts.VolumeAccessType.MOUNT,
			access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		self.addCleanup(lambda: self._client.NodeUnpublishVolume(VOL_ID, target_path))

		# Verify /mount publish dir exists
		env_dir = TestNodeService.driver_server.env_dir
		target_path_in_env_dir = os.path.join(env_dir, target_parent_dir[1:], 'mount')
		self.assertTrue(os.path.isdir(target_path_in_env_dir))

	@CatchRequestErrors
	def test_node_publish_volume_block(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/mount'
		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_parent_dir)
		self._client.NodePublishVolume(
			volume_id=VOL_ID,
			target_path=target_path,
			access_type=Consts.VolumeAccessType.BLOCK,
			access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		self.addCleanup(lambda: self._client.NodeUnpublishVolume(VOL_ID, target_path))

		env_dir = TestNodeService.driver_server.env_dir
		block_device_file_in_env_dir = os.path.join(env_dir, target_parent_dir[1:], 'mount')
		is_file = os.path.isfile(block_device_file_in_env_dir)
		self.assertTrue(is_file)

	@CatchRequestErrors
	def test_node_unpublish_volume_fs(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/mount'

		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_parent_dir)
		self._client.NodePublishVolume(
			volume_id=VOL_ID,
			target_path=target_path,
			access_type=Consts.VolumeAccessType.MOUNT,
			access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)

		self._client.NodeUnpublishVolume(volume_id=VOL_ID, target_path=target_path)
		env_dir = TestNodeService.driver_server.env_dir
		block_device_file_in_env_dir = os.path.join(env_dir, target_parent_dir[1:], 'mount')
		publish_path_exists = os.path.exists(block_device_file_in_env_dir)
		self.assertFalse(publish_path_exists)

	@CatchRequestErrors
	def test_node_unpublish_volume_block(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/mount'

		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_parent_dir)
		self._client.NodePublishVolume(
			volume_id=VOL_ID,
			target_path=target_path,
			access_type=Consts.VolumeAccessType.BLOCK,
			access_mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)

		self._client.NodeUnpublishVolume(volume_id=VOL_ID, target_path=target_path)
		env_dir = TestNodeService.driver_server.env_dir
		block_device_file_in_env_dir = os.path.join(env_dir, target_parent_dir[1:], 'mount')
		publish_path_exists = os.path.exists(block_device_file_in_env_dir)
		self.assertFalse(publish_path_exists)

	@CatchRequestErrors
	def test_node_expand_volume(self):
		def do_request():
			return self._client.NodeExpandVolume(volume_id=VOL_ID)

		self.assertReturnsGrpcError(do_request, StatusCode.INVALID_ARGUMENT, "Device not formatted with FileSystem")

	@CatchRequestErrors
	def test_change_mount_permissions(self):
		staging_target_path = STAGING_PATH_TEMPLATE.format(volume_id=VOL_ID)
		target_parent_dir = TARGET_PATH_PARENT_DIR_TEMPLATE.format(volume_id=VOL_ID, pod_id=DEFAULT_POD_ID)
		target_path = target_parent_dir + '/mount'

		TestNodeService.driver_server.add_nvmesh_device(VOL_ID)
		TestNodeService.driver_server.make_dir_in_env_dir(staging_target_path)
		TestNodeService.driver_server.make_dir_in_env_dir(target_parent_dir)

		expected_permission_mask = '600'

		mount_flags = [
			'nvmesh:chmod=%s' % (expected_permission_mask)
		]

		access_mode_obj = VolumeCapability.AccessMode(mode=VolumeCapability.AccessMode.SINGLE_NODE_WRITER)
		mount_req = VolumeCapability.MountVolume(fs_type='xfs', mount_flags=mount_flags)
		volume_capability = VolumeCapability(mount=mount_req, access_mode=access_mode_obj)

		req = NodePublishVolumeRequest(
			volume_id=VOL_ID,
			staging_target_path=staging_target_path,
			target_path=target_path,
			volume_capability=volume_capability,
			readonly=False
		)

		self._client.client.NodePublishVolume(req)

		env_dir = TestNodeService.driver_server.env_dir
		block_device_file_in_env_dir = os.path.join(env_dir, target_parent_dir[1:], 'mount')
		publish_path_exists = os.path.exists(block_device_file_in_env_dir)
		self.assertTrue(publish_path_exists)

		permissions_found = TestNodeService.driver_server.run_command_in_container(['stat', '--format', '%a', target_path])
		self.assertEquals(permissions_found.strip(), expected_permission_mask)


class TestNodeServiceGracefulShutdown(TestCaseWithServerRunning):
	def test_node_graceful_shutdown(self):
		topology = {
			'type': consts.TopologyType.MULTIPLE_NVMESH_CLUSTERS,
			'zones': TOPOLOGY_SINGLE_ZONE['zones']
		}
		config = {'topology': json.dumps(topology)}
		driver_server = start_containerized_server(Consts.DriverType.Node, config=config, hostname='node-1')
		config['SOCKET_PATH'] = 'unix://%s' % driver_server.csi_socket_path
		ConfigLoaderMock(config).load()
		client = NodeClient()

		results = []
		def run_get_info(results):
			log.debug('Calling GetInfo')
			res = client.NodeGetInfo()
			results.append(res.node_id)

		thread = Thread(target=run_get_info, args=(results,))
		thread.start()

		log.debug('Stopping the gRPC server')
		driver_server.stop()

		thread.join()

		self.assertEquals(len(results), 1)


if __name__ == '__main__':
	unittest.main()
