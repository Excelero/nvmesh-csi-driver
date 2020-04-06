import logging
import sys
import time
import unittest

import kubernetes
from NVMeshSDK.ConnectionManager import ConnectionManager, ManagementTimeout
from kubernetes import client, config

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.Consts import RAIDLevels
from NVMeshSDK.MongoObj import MongoObj

TEST_NAMESPACE = 'nvmesh-csi-testing'
NVMESH_MGMT_ADDRESS = 'https://n115:4000'

config.load_kube_config()

core_api = client.CoreV1Api()
storage_api = client.StorageV1Api()

def create_logger():
	logger_instance = logging.getLogger('test')
	logger_instance.setLevel(logging.DEBUG)

	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger_instance.addHandler(handler)

	return logger_instance

logger = create_logger()


class TestError(Exception):
	pass

class CollectCsiLogsTestResult(unittest.TestResult):
	def addFailure(self, test, err):
		# when a test case fails
		log_lines = KubeUtils.get_logs_from_csi_controller(max_lines=30)

		print('========================= BEGIN - NVMesh CSI Controller - Last Logs Lines =========================')
		for line in log_lines:
			print(line)
		print('============================= END - NVMesh CSI Driver Controller Logs ================================')

		super(CollectCsiLogsTestResult, self).addFailure(test, err)

	def addError(self, test, err):
		# when a test case raises an error
		print("Test {} - Error: {}".format(test, err))
		super(CollectCsiLogsTestResult, self).addError(test, err)

class TestUtils(object):
	@staticmethod
	def assert_equal(a, b, message):
		if not message:
			message = 'Not Equal'
		if a != b:
			raise TestError('{}: Expected {} but got {}'.format(message, a, b))

	@staticmethod
	def get_logger():
		return logger

	@staticmethod
	def get_test_namespace():
		return TEST_NAMESPACE

	@staticmethod
	def run_unittest():
		unittest.main(testRunner=unittest.TextTestRunner(resultclass=CollectCsiLogsTestResult))


class KubeUtils(object):
	@staticmethod
	def clear_environment():
		ns = TestUtils.get_test_namespace()
		try:
			# This will also delete all deployments and pods under the namespace
			# * But not storage classes and persistent volumes (they are global)
			KubeUtils.delete_namespace(ns)
			KubeUtils.create_namespace(ns)
		except kubernetes.client.rest.ApiException as ex:
			logger.exception(ex)

		# Verify no PersistentVolumes
		pv_list = core_api.list_persistent_volume()
		for item in pv_list.items:
			logger.debug('found stale pv %s deleting it..', item.metadata.name)
			core_api.delete_persistent_volume(item.metadata.name)

		# Verify no Extra Storage Classes
		KubeUtils.delete_all_non_default_storage_classes()

	@staticmethod
	def delete_all_non_default_storage_classes():
		sc_list = storage_api.list_storage_class()
		for storage_class in sc_list.items:
			name = storage_class.metadata.name
			if not name.startswith('nvmesh-'):
				logger.debug('Deleting StorageClass {}'.format(name))
				storage_api.delete_storage_class(name)

	@staticmethod
	def create_namespace(ns):
		namespace_obj = {
			'metadata': {
				'name': ns
			}
		}
		core_api.create_namespace(namespace_obj)

	@staticmethod
	def delete_namespace(ns):
		logger.info('Deleting everything under namespace {}'.format(ns))
		try:
			core_api.delete_namespace(ns)
		except kubernetes.client.rest.ApiException as ex:
			pass
		attempts = 20
		found = True
		while attempts > 0 and found:
			found = False
			ns_list = core_api.list_namespace()
			for ns_item in ns_list.items:
				if ns_item.metadata.name == ns:
					found = True

		if found:
			raise TestError('Timed out waiting for namespace {} to be deleted'.format(ns))

	@staticmethod
	def get_pv_name_from_pvc(pvc_name):
		pvc = KubeUtils.get_pvc_by_name(pvc_name)
		return pvc.spec.volume_name

	@staticmethod
	def get_storage_class(name, params):
		return {
			'apiVersion': 'storage.k8s.io/v1',
			'kind': 'StorageClass',
			'metadata': {
			  'name': name,
			  'namespace': TestUtils.get_test_namespace()
			},
			'provisioner': 'nvmesh-csi.excelero.com',
			'allowVolumeExpansion': True,
			'volumeBindingMode': 'Immediate',
			'parameters': params
		}

	@staticmethod
	def create_storage_class(name, params):
		try:
			sc = KubeUtils.get_storage_class(name, params)
			return storage_api.create_storage_class(sc)
		except kubernetes.client.rest.ApiException as ex:
			logger.exception(ex)
			msg = 'Failed to create storage class {}'.format(name)
			raise TestError(msg)

	@staticmethod
	def get_pvc_by_name(pvc_name):
		pvcs_res = core_api.list_persistent_volume_claim_for_all_namespaces()

		for pvc in pvcs_res.items:
			if pvc.metadata.name == pvc_name:
				return pvc

	@staticmethod
	def get_pv_by_name(pv_name):
		pv_res = core_api.list_persistent_volume()

		for pv in pv_res.items:
			if pv.metadata.name == pv_name:
				return pv

	@staticmethod
	def wait_for_pvc_to_bound(pvc_name, attempts=5):
		while attempts > 0:
			pvc = KubeUtils.get_pvc_by_name(pvc_name)
			if not pvc:
				print('Waiting for pvc {} to be created'.format(pvc_name))
			elif pvc.status.phase == 'Bound':
				print('pvc {} is Bound'.format(pvc_name))
				return
			else:
				print('Waiting for pvc {} to be Bound to a PersistentVolume. current status.phase = {} '.format(pvc_name, pvc.status.phase))

			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pvc {} to bound'.format(pvc_name))

	@staticmethod
	def get_logs_from_csi_controller(max_lines=None):
		pod_name = None
		pods = core_api.list_namespaced_pod('nvmesh-csi')
		for pod in pods.items:
			if 'nvmesh-csi-controller' in pod.metadata.name:
				pod_name = pod.metadata.name
				break

		api_response = core_api.read_namespaced_pod_log(name=pod_name, container='nvmesh-csi-driver', namespace='nvmesh-csi')
		log_lines = api_response.split('\n')

		if max_lines:
			log_lines = log_lines[-max_lines:]

		return log_lines

	@staticmethod
	def delete_storage_class(name):
		return storage_api.delete_storage_class(name)

	@staticmethod
	def delete_pvc(pvc_name):
		core_api.delete_namespaced_persistent_volume_claim(pvc_name, namespace=TEST_NAMESPACE)

class NVMeshUtils(object):
	@staticmethod
	def delete_all_nvmesh_volumes():
		projection = [MongoObj(field='_id', value=1)]
		err, volume_list = VolumeAPI(NVMESH_MGMT_ADDRESS).get(projection=projection)
		if len(volume_list) != 0:
			err, out = VolumeAPI(NVMESH_MGMT_ADDRESS).delete([ vol._id for vol in volume_list ])
			if err:
				raise TestError('Failed to delete NVMesh volumes. Error: {}'.format(err))

			for vol_res in out:
				if not vol_res['success']:
					raise TestError('Failed to delete NVMesh volume {}. Error: {}'.format(vol_res['_id'], vol_res['error']))

	@staticmethod
	def init_nvmesh_sdk():
		connected = False

		# try until able to connect to NVMesh Management
		while not connected:
			try:
				ConnectionManager.getInstance(managementServer=[NVMESH_MGMT_ADDRESS], logToSysLog=False)
				connected = ConnectionManager.getInstance().isAlive()
			except ManagementTimeout as ex:
				logger.info("Waiting for NVMesh Management server on {}".format(NVMESH_MGMT_ADDRESS))
				time.sleep(1)

		logger.info("Connected to NVMesh Management server on {}".format(ConnectionManager.getInstance().managementServer))


	@staticmethod
	def csi_id_to_nvmesh_name(co_vol_name):
		# Nvmesh vol name / id cannot be longer than 23 characters
		return 'csi-' + co_vol_name[4:22]

	@staticmethod
	def get_nvmesh_volume_by_name(nvmesh_vol_name):
		filter_obj = [MongoObj(field='_id', value=nvmesh_vol_name)]
		err, out = VolumeAPI(NVMESH_MGMT_ADDRESS).get(filter=filter_obj)
		if len(out) == 0:
			return None
		else:
			return out[0]

	@staticmethod
	def parse_raid_type(raid_type_string):
		raid_type_string = raid_type_string.lower()

		raid_converter = {
			'concatenated': RAIDLevels.CONCATENATED,
			'lvm': RAIDLevels.CONCATENATED,
			'jbod': RAIDLevels.CONCATENATED,
			'mirrored': RAIDLevels.MIRRORED_RAID_1,
			'raid1': RAIDLevels.MIRRORED_RAID_1,
			'raid10': RAIDLevels.STRIPED_AND_MIRRORED_RAID_10,
			'raid0': RAIDLevels.STRIPED_RAID_0,
			'ec': RAIDLevels.ERASURE_CODING
		}

		if raid_type_string not in raid_converter:
			raise ValueError('Unknown RAID Type %s' % raid_type_string)

		parsed_value = raid_converter[raid_type_string]
		return parsed_value

	@staticmethod
	def wait_for_nvmesh_volume(nvmesh_vol_name, attempts=5):
		while attempts > 0:
			volume = NVMeshUtils.get_nvmesh_volume_by_name(nvmesh_vol_name)
			if not volume:
				logger.info('Waiting for NVMesh Volume {} to be created'.format(nvmesh_vol_name))
			else:
				logger.info('NVMesh Volume {} created'.format(nvmesh_vol_name))
				return

			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for NVMesh Volume {} to be created'.format(nvmesh_vol_name))

# Connect To Management
NVMeshUtils.init_nvmesh_sdk()