import logging
import subprocess
import sys
import time
import unittest

import kubernetes
from kubernetes.client.rest import ApiException

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

class TestConfig(object):
	NumberOfVolumes = 1
	SkipECVolumes = True

def create_logger():
	logger_instance = logging.getLogger('test')
	logger_instance.setLevel(logging.DEBUG)

	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(logging.DEBUG)

	# short formatter
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%H:%M:%S")

	# long formatter
	#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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

		logger.debug('========================= BEGIN - NVMesh CSI Controller - Last Logs Lines =========================')
		for line in log_lines:
			logger.debug(line)
		logger.debug('============================= END - NVMesh CSI Driver Controller Logs ================================')

		super(CollectCsiLogsTestResult, self).addFailure(test, err)

	def addError(self, test, err):
		# when a test case raises an error
		logger.error("Test {} - Error: {}".format(test, err))
		super(CollectCsiLogsTestResult, self).addError(test, err)

class TestUtils(object):
	@staticmethod
	def get_logger():
		return logger

	@staticmethod
	def get_test_namespace():
		return TEST_NAMESPACE

	@staticmethod
	def run_unittest():
		unittest.main(testRunner=unittest.TextTestRunner(resultclass=CollectCsiLogsTestResult))

	@staticmethod
	def clear_environment():
		# Kubernetes Cleanup
		KubeUtils.delete_all_pods()
		KubeUtils.delete_all_pvcs()
		KubeUtils.delete_all_non_default_storage_classes()

		# NVMesh Cleanup
		NVMeshUtils.delete_all_nvmesh_volumes()

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
	def get_nvmesh_vol_name_from_pvc_name(pvc_name):
		pv_name = KubeUtils.get_pv_name_from_pvc(pvc_name)
		nvmesh_vol_name = NVMeshUtils.csi_id_to_nvmesh_name(pv_name)
		return nvmesh_vol_name

	@staticmethod
	def get_pv_name_from_pvc(pvc_name):
		pvc = KubeUtils.get_pvc_by_name(pvc_name)
		return pvc.spec.volume_name

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
	def get_storage_class(name, params):
		return {
			'apiVersion': 'storage.k8s.io/v1',
			'kind': 'StorageClass',
			'metadata': {
			  'name': name,
			  'namespace': TEST_NAMESPACE
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
		pvcs_res = core_api.list_namespaced_persistent_volume_claim(TEST_NAMESPACE, field_selector='metadata.name={}'.format(pvc_name))

		for pvc in pvcs_res.items:
			if pvc.metadata.name == pvc_name:
				return pvc

	@staticmethod
	def get_pv_by_name(pv_name):
		pv_res = core_api.list_persistent_volume(field_selector='metadata.name={}'.format(pv_name))

		for pv in pv_res.items:
			if pv.metadata.name == pv_name:
				return pv

	@staticmethod
	def wait_for_pvc_to_bound(pvc_name, attempts=5):
		while attempts > 0:
			pvc = KubeUtils.get_pvc_by_name(pvc_name)
			if not pvc:
				logger.debug('Waiting for pvc {} to be created'.format(pvc_name))
			elif pvc.status.phase == 'Bound':
				logger.info('pvc {} is Bound'.format(pvc_name))
				return
			else:
				logger.debug('Waiting for pvc {} to be Bound to a PersistentVolume. current status.phase = {} '.format(pvc_name, pvc.status.phase))

			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pvc {} to bound'.format(pvc_name))

	@staticmethod
	def wait_for_pvc_to_extend(pvc_name, new_size, attempts=10):
		while attempts > 0:
			pvc = KubeUtils.get_pvc_by_name(pvc_name)
			current_size = pvc.spec.resources.requests['storage']

			if current_size !=  new_size:
				logger.debug('Waiting for pvc {} to be extended to {}. current size is {}'.format(pvc_name, new_size, current_size))
			else:
				logger.info('pvc {} extended'.format(pvc_name))
				return

			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pvc {} to extend'.format(pvc_name))

	@staticmethod
	def wait_for_pvc_to_delete(pvc_name, attempts=15):
		while attempts > 0:
			pvc = KubeUtils.get_pvc_by_name(pvc_name)
			if not pvc:
				return

			logger.debug('Waiting for pvc {} to be deleted'.format(pvc_name))
			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pvc {} to delete'.format(pvc_name))

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
		try:
			core_api.delete_namespaced_persistent_volume_claim(pvc_name, namespace=TEST_NAMESPACE)
		except ApiException as apiEx:
			if apiEx.reason == 'Not Found':
				return
			else:
				raise

	@staticmethod
	def delete_all_pvcs():
		pvcs_res= core_api.list_namespaced_persistent_volume_claim(TEST_NAMESPACE)

		for pvc in pvcs_res.items:
			core_api.delete_namespaced_persistent_volume_claim(pvc.metadata.name, namespace=TEST_NAMESPACE)

		for pvc in pvcs_res.items:
			KubeUtils.wait_for_pvc_to_delete(pvc.metadata.name)

	@staticmethod
	def get_pvc_template(pvc_name, storage_class_name, access_modes=None, storage='3Gi'):
		pvc = {
			'apiVersion': 'v1',
			'kind': 'PersistentVolumeClaim',
			'metadata': {
				'name': pvc_name,
				'namespace': TestUtils.get_test_namespace()
			},
			'spec': {
				'accessModes': access_modes or ['ReadWriteOnce'],
				'resources': {
					'requests': {
						'storage': storage
					}
				},
				'storageClassName': storage_class_name
			}
		}

		return pvc

	@staticmethod
	def create_pvc(pvc):
		return core_api.create_namespaced_persistent_volume_claim(TEST_NAMESPACE, pvc)

	@staticmethod
	def get_pod_template(pod_name, spec, app_label=None):
		pod = {
			'apiVersion': 'v1',
			'kind': 'Pod',
			'metadata': {
				'name': pod_name,
				'namespace': TEST_NAMESPACE,
				'labels': {
					'app': app_label or pod_name
				}
			},
			'spec': spec
		}

		return pod

	@staticmethod
	def create_pod(pod):
		core_api.create_namespaced_pod(TEST_NAMESPACE, pod)

	@staticmethod
	def delete_pod(pod_name):
		try:
			logger.info('Deleting Pod {}'.format(pod_name))
			core_api.delete_namespaced_pod(pod_name, TEST_NAMESPACE)
		except ApiException as apiEx:
			if apiEx.reason == 'Not Found':
				return
			else:
				raise

	@staticmethod
	def wait_for_pod_to_delete(pod_name, attempts=60):
		while attempts > 0:
			pod = KubeUtils.get_pod_by_name(pod_name)
			if not pod:
				return

			logger.debug('Waiting for pod {} to be deleted'.format(pod_name))
			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pod {} to delete'.format(pod_name))

	@staticmethod
	def get_pod_by_name(pod_name):
		field_selector = 'metadata.name={}'.format(pod_name)
		pods = core_api.list_namespaced_pod(TEST_NAMESPACE, field_selector=field_selector)

		for pod in pods.items:
			if pod.metadata.name == pod_name:
				return pod

	@staticmethod
	def delete_all_pods():
		pods = core_api.list_namespaced_pod(TEST_NAMESPACE)

		for pod in pods.items:
			KubeUtils.delete_pod(pod.metadata.name)

		for pod in pods.items:
			KubeUtils.wait_for_pod_to_delete(pod.metadata.name)

	@staticmethod
	def patch_pvc(pvc_name, pvc_patch):
		core_api.patch_namespaced_persistent_volume_claim(pvc_name, TEST_NAMESPACE, pvc_patch)

	@staticmethod
	def run_command_in_container(pod_name, command):
		cmd = 'kubectl exec -n {ns} {pod} -- {cmd}'.format(ns=TEST_NAMESPACE, pod=pod_name, cmd=command)
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p.communicate()
		return stdout

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
					if 'Couldn\'t find the specified volume' not in vol_res['error']:
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

	@staticmethod
	def wait_for_nvmesh_vol_properties(nvmesh_vol_name, params, unittest_instance, attempts=1):
		while attempts:
			attempts = attempts - 1
			volume = NVMeshUtils.get_nvmesh_volume_by_name(nvmesh_vol_name)

			for key, value in params.iteritems():
				if key == 'raidLevel':
					expected_val = NVMeshUtils.parse_raid_type(value)
					nvmesh_key = 'RAIDLevel'
				elif key in ['stripeWidth', 'stripeSize', 'numberOfMirrors']:
					expected_val = int(value)
					nvmesh_key = key
				else:
					expected_val = value
					nvmesh_key = key

				nvmesh_value = getattr(volume, nvmesh_key)
				if expected_val != nvmesh_value:
					logger.debug('Waiting for {key}={val} to be {key}={expected_val}'.format(
						key=nvmesh_key,val=nvmesh_value,expected_val=expected_val))
					if not attempts:
						unittest_instance.assertEqual(expected_val, nvmesh_value, 'Wrong value in Volume {}'.format(nvmesh_key))
				else:
					return
			time.sleep(1)


# Connect To Management
NVMeshUtils.init_nvmesh_sdk()