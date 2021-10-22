import logging
import os
import subprocess
import sys
import time
import unittest
import yaml
from os import environ

import kubernetes
from kubernetes.client.rest import ApiException

from kubernetes import client, config
from kubernetes.stream import stream

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.Consts import RAIDLevels
from NVMeshSDK.MongoObj import MongoObj
from driver import consts

SERVICE_ACCOUNT_NAME = 'csi-driver-test-account'
TEST_LABEL_KEY = 'nvmesh-csi-testing'

try:
	config.load_incluster_config()
except:
	config.load_kube_config()

configuration = client.Configuration()
configuration.verify_ssl = False
configuration.debug = False
client.Configuration.set_default(configuration)
core_api = client.CoreV1Api()
storage_api = client.StorageV1Api()
apps_api = client.AppsV1Api()

IO_TEST_IMAGE_NAME = 'excelero/io-tools:1.0.0'

class TestConfig(object):
	TestNamespace = 'test-csi-driver-integration'
	ManagementServers = ['localhost:4000']
	NumberOfVolumes = 3
	SkipECVolumes = True
	SkipTopology = False
	Topology = None

def parse_config_from_file(test_config):
	try:
		conf = test_config['integration']
		TestConfig.TestNamespace = conf.get('testNamespace', TestConfig.TestNamespace)
		TestConfig.ManagementServers = conf.get('managementServers', TestConfig.ManagementServers)
		TestConfig.NumberOfVolumes = conf.get('numberOfVolumes', TestConfig.NumberOfVolumes)
		TestConfig.SkipECVolumes = conf.get('skipECVolumes', TestConfig.SkipECVolumes)
		TestConfig.SkipTopology = conf.get('skipTopology', TestConfig.SkipTopology)
		TestConfig.Topology = conf.get('topology')
	except Exception as ex:
		print('Failed to parse test config. Error: %s' % ex)
		raise

def load_test_config_file():
	test_config_path = environ.get('TEST_CONFIG_PATH') or os.path.join(os.getcwd(), '../config.yaml')
	try:
		with open(test_config_path, 'r') as fp:
			test_config = yaml.safe_load(fp)
			if not test_config:
				raise ValueError('Empty Config File')
	except Exception as ex:
		print('Failed to load test config file at %s. Error: %s' % (test_config_path, ex))
		raise

	parse_config_from_file(test_config)

def load_test_config_values_from_env_vars():
	if 'num_of_volumes' in environ:
		try:
			TestConfig.NumberOfVolumes = int(environ['num_of_volumes'])
		except Exception as ex:
			raise ValueError("Failed to parse env var num_of_volumes of %s. Parse Error: %s" % (environ['num_of_volumes'], ex))

	if 'no_ec_volumes' in environ:
		str_value = environ['no_ec_volumes'].lower()
		if str_value == 'true':
			TestConfig.SkipECVolumes = True
		elif str_value == 'false':
			TestConfig.SkipECVolumes = False
		else:
			raise ValueError("Failed to parse env var no_ec_volumes of %s. allowed values are true or false", environ['no_ec_volumes'])

def print_test_config():
	print('TestConfig:')
	for field, value in TestConfig.__dict__.items():
		if not field.startswith('_'):
			print('  {}={}'.format(field, value))

load_test_config_file()
load_test_config_values_from_env_vars()
print_test_config()

def create_logger():
	logger_instance = logging.getLogger('test')

	handler = logging.StreamHandler(sys.stdout)
	stdout_log_level = environ.get('TEST_STDOUT_LOG_LEVEL', None)
	handler.setLevel(stdout_log_level or logging.DEBUG)
	logger_instance.setLevel(stdout_log_level or logging.DEBUG)
	sdk_logger = logging.getLogger('NVMeshSDK')
	sdk_logger.setLevel(stdout_log_level or logging.DEBUG)
	formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%H:%M:%S")

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
		return TestConfig.TestNamespace

	@staticmethod
	def run_unittest():
		unittest.main(verbosity=2, testRunner=unittest.TextTestRunner(resultclass=CollectCsiLogsTestResult))

	@staticmethod
	def clear_environment():
		# Kubernetes Cleanup
		KubeUtils.delete_all_deployments()
		KubeUtils.delete_all_pods()
		KubeUtils.delete_all_pvcs()
		KubeUtils.delete_all_non_default_storage_classes()
		KubeUtils.delete_all_testing_pv()

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
	def taint_node(node_name, key, value, effect=None):
		taint = {"key": key, "value": value}
		if effect:
			taint['effect'] = effect
		core_api.patch_node(node_name, {"spec": {"taints": [taint]}})

	@staticmethod
	def node_prevent_schedule(node_name):
		KubeUtils.taint_node(node_name, "prevent-scheduling", "1", "NoSchedule")

	@staticmethod
	def node_allow_schedule(node_name):
		node_list = core_api.list_node(field_selector='metadata.name={}'.format(node_name))
		if not node_list:
			Exception("node %s Not found" % node_name)

		node = node_list.items[0]
		taints = []
		for taint in node.spec.taints:
			if taint.key != "prevent-scheduling":
				taints.append(taint)
		core_api.patch_node(node_name, {"spec": { "taints": taints }})

	@staticmethod
	def node_allow_schedule_all_nodes(key, value, effect):
		node_list = core_api.list_node()
		for node in node_list.items:
			KubeUtils.node_allow_schedule(node.metadata.name)

	@staticmethod
	def taint_all_nodes(key, value, effect):
		node_list = core_api.list_node()
		for node in node_list.items:
			KubeUtils.taint_node(node.metadata.name, key, value, effect)

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
		sc_list = storage_api.list_storage_class(label_selector=TEST_LABEL_KEY)
		for storage_class in sc_list.items:
			name = storage_class.metadata.name
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
	def get_storage_class(name, params, **kwargs):
		sc = {
			'apiVersion': 'storage.k8s.io/v1',
			'kind': 'StorageClass',
			'metadata': {
			  'name': name,
			  'namespace': TestConfig.TestNamespace,
			  'labels': KubeUtils.get_test_labels()
			},
			'provisioner': 'nvmesh-csi.excelero.com',
			'allowVolumeExpansion': True,
			'volumeBindingMode': 'Immediate',
			'reclaimPolicy': 'Delete',
			'parameters': params
		}

		sc.update(kwargs)
		return sc

	@staticmethod
	def create_storage_class(name, params, **kwargs):
		try:
			sc = KubeUtils.get_storage_class(name, params, **kwargs)
			return storage_api.create_storage_class(sc)
		except kubernetes.client.rest.ApiException as ex:
			logger.exception(ex)
			msg = 'Failed to create storage class {}'.format(name)
			raise TestError(msg)

	@staticmethod
	def create_storage_class_with_cleanup(unittest_instance, name, params, **kwargs):
		sc = KubeUtils.create_storage_class(name, params, **kwargs)
		unittest_instance.addCleanup(lambda: KubeUtils.delete_storage_class(name))
		return sc

	@staticmethod
	def get_pvc_by_name(pvc_name):
		pvcs_res = core_api.list_namespaced_persistent_volume_claim(TestConfig.TestNamespace, field_selector='metadata.name={}'.format(pvc_name))

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
	def wait_for_pvc_to_bound(pvc_name, attempts=15):
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
	def wait_for_pvc_to_delete(pvc_name, attempts=30):
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
			core_api.delete_namespaced_persistent_volume_claim(pvc_name, namespace=TestConfig.TestNamespace)
		except ApiException as apiEx:
			if apiEx.reason == 'Not Found':
				return
			else:
				raise

	@staticmethod
	def delete_all_pvcs():
		pvcs_res= core_api.list_namespaced_persistent_volume_claim(TestConfig.TestNamespace, label_selector=TEST_LABEL_KEY)

		for pvc in pvcs_res.items:
			core_api.delete_namespaced_persistent_volume_claim(pvc.metadata.name, namespace=TestConfig.TestNamespace)

		for pvc in pvcs_res.items:
			KubeUtils.wait_for_pvc_to_delete(pvc.metadata.name)

	@staticmethod
	def get_pvc_template(pvc_name, storage_class_name, access_modes=None, storage='3Gi', volumeMode='Filesystem', **kwargs):
		pvc = {
			'apiVersion': 'v1',
			'kind': 'PersistentVolumeClaim',
			'metadata': {
				'name': pvc_name,
				'namespace': TestUtils.get_test_namespace(),
				'labels': KubeUtils.get_test_labels()
			},
			'spec': {
				'accessModes': access_modes or ['ReadWriteOnce'],
				'volumeMode': volumeMode,
				'resources': {
					'requests': {
						'storage': storage
					}
				},
				'storageClassName': storage_class_name
			}
		}

		pvc.update(kwargs)
		return pvc

	@staticmethod
	def create_pvc(pvc):
		logger.info('Creating pvc {}'.format(pvc['metadata']['name']))
		return core_api.create_namespaced_persistent_volume_claim(TestConfig.TestNamespace, pvc)

	@staticmethod
	def get_pod_template(pod_name, spec, app_label=None):
		labels = KubeUtils.get_test_labels()
		labels.update({
			'app': app_label or pod_name
		})

		pod = {
			'apiVersion': 'v1',
			'kind': 'Pod',
			'metadata': {
				'name': pod_name,
				'namespace': TestConfig.TestNamespace,
				'labels': labels
			},
			'spec': spec
		}

		return pod

	@staticmethod
	def create_pod(pod):
		logger.info('Creating pod {}'.format(pod['metadata']['name']))
		core_api.create_namespaced_pod(TestConfig.TestNamespace, pod)

	@staticmethod
	def delete_pod(pod_name):
		try:
			logger.info('Deleting Pod {}'.format(pod_name))
			core_api.delete_namespaced_pod(pod_name, TestConfig.TestNamespace)
		except ApiException as apiEx:
			if apiEx.reason == 'Not Found':
				return
			else:
				raise

	@staticmethod
	def wait_for_pod_to_be_running(pod_name, attempts=60):
		return KubeUtils.wait_for_pod_status(pod_name, 'Running', attempts)

	@staticmethod
	def wait_for_pod_to_fail(pod_name, attempts=10):
		while attempts > 0:
			pod = KubeUtils.get_pod_by_name(pod_name)
			if pod:
				status = pod.status.phase
				if status == 'Running':
					raise TestError('Expected pod {} to fail. but it is running'.format(pod_name))

			logger.debug('Waiting to make sure pod {} does not run'.format(pod_name))
			attempts = attempts - 1
			time.sleep(1)

	@staticmethod
	def wait_for_pod_to_complete(pod_name, attempts=60):
		return KubeUtils.wait_for_pod_status(pod_name, 'Succeeded', attempts)

	@staticmethod
	def wait_for_pod_status(pod_name, expected_status, attempts=90):
		status = None
		pod = None
		while attempts > 0:
			pod = KubeUtils.get_pod_by_name(pod_name)
			if pod:
				status = pod.status.phase
				if status == expected_status:
					logger.info('Pod {} is {}'.format(pod_name, expected_status))
					return
			logger.debug('Waiting for pod {} to be {}, current status: {}'.format(pod_name, expected_status, status))
			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pod {} to be {}, current status: {}, reason: {}'.format(pod_name, expected_status, status, pod.status.reason))

	@staticmethod
	def delete_pod_and_wait(pod_name, attempts=60):
		KubeUtils.delete_pod(pod_name)
		KubeUtils.wait_for_pod_to_delete(pod_name, attempts)

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
		pods = core_api.list_namespaced_pod(TestConfig.TestNamespace, field_selector=field_selector)

		for pod in pods.items:
			if pod.metadata.name == pod_name:
				return pod

	@staticmethod
	def delete_all_pods():
		pods = core_api.list_namespaced_pod(TestConfig.TestNamespace, label_selector=TEST_LABEL_KEY)

		for pod in pods.items:
			KubeUtils.delete_pod(pod.metadata.name)

		for pod in pods.items:
			KubeUtils.wait_for_pod_to_delete(pod.metadata.name)

	@staticmethod
	def delete_all_deployments():
		deps = apps_api.list_namespaced_deployment(TestConfig.TestNamespace, label_selector=TEST_LABEL_KEY)

		for deployment in deps.items:
			name = deployment.metadata.name
			logger.info("Deleting Deployment {}".format(name))
			KubeUtils.delete_deployment(name)

	@staticmethod
	def patch_pvc(pvc_name, pvc_patch):
		core_api.patch_namespaced_persistent_volume_claim(pvc_name, TestConfig.TestNamespace, pvc_patch)

	@staticmethod
	def run_command_in_container(pod_name, command_as_arr):
		response = stream(core_api.connect_get_namespaced_pod_exec,
					pod_name,
					TestConfig.TestNamespace,
					command=command_as_arr,
					stderr=True, stdin=False,
					stdout=True, tty=False)
		logger.debug("run_command_in_container response: %s" % response)
		return response

	@staticmethod
	def get_fs_consumer_pod_template(pod_name, pvc_name):
		spec = {
			'containers': [
				{
					'name': 'fs-consumer',
					'image': IO_TEST_IMAGE_NAME,
					'env': [
						{
							'name': 'VOLUME_TYPE',
							'value': 'Filesystem'
						},
						{
							'name': 'VOLUME_PATH',
							'value': '/mnt/vol'
						}
					],
					'volumeMounts': [
						{
							'name': 'fs-volume',
							'mountPath': '/mnt/vol'
						}
					]
				}
			],
			'volumes': [
				{
					'name': 'fs-volume',
					'persistentVolumeClaim': {
						'claimName': pvc_name
					}
				}
			]
		}

		pod = KubeUtils.get_pod_template(pod_name, spec)
		return pod

	@staticmethod
	def get_shell_pod_template(pod_name, pvc_name, cmd, volume_mode_block=False):
		spec = {
			'restartPolicy': 'OnFailure',
			'containers': [
				{
					'name': 'container-{}'.format(pod_name),
					'image': 'alpine',
					'command': ["/bin/sh"],
					'args': ["-c", cmd],
					'volumeMounts': [
						{
							'name': 'vol',
							'mountPath': '/vol'
						}
					]
				}
			],
			'volumes': [
				{
					'name': 'vol',
					'persistentVolumeClaim': {
						'claimName': pvc_name
					}
				}
			]
		}

		if volume_mode_block:
			del spec['containers'][0]['volumeMounts']
			spec['containers'][0]['volumeDevices'] = [
				{
					'name': 'vol',
					'devicePath': '/vol'
				}
			]

		pod = KubeUtils.get_pod_template(pod_name, spec)
		return pod

	@staticmethod
	def get_block_consumer_pod_template(pod_name, pvc_name):
		spec = {
			'containers': [
				{
					'name': 'block-volume-consumer',
					'image': IO_TEST_IMAGE_NAME,
					'env': [
						{
							'name': 'VOLUME_TYPE',
							'value': 'Block'
						},
						{
							'name': 'VOLUME_PATH',
							'value': '/dev/my_block_dev'
						}
					],
					'volumeDevices': [
						{
							'name': 'block-volume',
							'devicePath': '/dev/my_block_dev'
						}
					]
				}
			],
			'volumes': [
				{
					'name': 'block-volume',
					'persistentVolumeClaim': {
						'claimName': pvc_name
					}
				}
			]
		}

		pod = KubeUtils.get_pod_template(pod_name, spec)
		return pod

	@staticmethod
	def get_deployment_template(name, pod_spec, replicas=1):
		deployment = {
			"apiVersion": "apps/v1",
			"kind": "Deployment",
			"metadata": {
				"name": name,
				"namespace": TestConfig.TestNamespace,
				"labels": {
					"app": "test-container-migration",
					TEST_LABEL_KEY: ""
				}
			},
			"spec": {
				"replicas": replicas,
				"selector": {
					"matchLabels": {
						"app": name
					}
				},
				"template": {
					"metadata": {
						"labels": {
							"app": name,
							TEST_LABEL_KEY: ""
						}
					},
					"spec": pod_spec
				}
			}
		}

		return deployment

	@staticmethod
	def get_pod_log(pod_name):
		response = core_api.read_namespaced_pod_log(pod_name, TestConfig.TestNamespace)
		return response

	@staticmethod
	def create_deployment(deployment):
		return apps_api.create_namespaced_deployment(TestConfig.TestNamespace, deployment)

	@staticmethod
	def create_pvc_and_wait_to_bound(unittest_instance, pvc_name, sc_name, attempts=15, **kwargs):
		KubeUtils.create_pvc_with_cleanup(unittest_instance, pvc_name, sc_name, **kwargs)
		KubeUtils.wait_for_pvc_to_bound(pvc_name, attempts=attempts)

	@staticmethod
	def create_pvc_with_cleanup(unittest_instance, pvc_name, sc_name, **kwargs):
		pvc_yaml = KubeUtils.get_pvc_template(pvc_name, sc_name, **kwargs)
		KubeUtils.create_pvc(pvc_yaml)

		def cleanup_volume():
			KubeUtils.delete_pvc(pvc_name)
			KubeUtils.wait_for_pvc_to_delete(pvc_name, attempts=60)

		unittest_instance.addCleanup(cleanup_volume)

		return cleanup_volume

	@staticmethod
	def delete_deployment(name):
		return apps_api.delete_namespaced_deployment(name, TestConfig.TestNamespace)

	@staticmethod
	def get_deployment(dep_name):
		dep_list = apps_api.list_namespaced_deployment(TestConfig.TestNamespace, field_selector='metadata.name={}'.format(dep_name))
		return dep_list.items[0]

	@staticmethod
	def get_pods_for_deployment(deployment_name):
		pod_list = core_api.list_namespaced_pod(TestConfig.TestNamespace, label_selector='app={}'.format(deployment_name))
		return pod_list.items

	@staticmethod
	def wait_for_block_device_resize(unittest_instance, pod_name, nvmesh_vol_name, new_size, attempts=30):
		size = None

		while attempts:
			attempts = attempts - 1
			# check block device size in container
			stdout = KubeUtils.run_command_in_container(pod_name, ['lsblk'])
			if stdout:
				lines = stdout.split('\n')
				for line in lines:
					if nvmesh_vol_name in line:
						logger.debug('found nvmesh volume line = %s' % line)
						columns = line.split()
						size = columns[3]
						break
			if size == new_size:
				# success
				logger.info('Block device on {} was extended to {}'.format(pod_name, new_size))
				return
			else:
				logger.debug('Waiting for block device to extend to {} current size is {}'.format(new_size, size))
				logger.debug('lsblk output = %s' % stdout)
			time.sleep(1)

		unittest_instance.assertEqual(size, new_size, 'Timed out waiting for Block Device to resize')

	@staticmethod
	def get_pv_for_static_provisioning(pv_name, nvmesh_volume_name, accessModes, sc_name, volume_size, volumeMode='Block'):
		return \
		{
			'apiVersion': 'v1',
			'kind': 'PersistentVolume',
			'metadata': {
				'name': pv_name
			},
			'spec': {
				'accessModes': accessModes,
				'persistentVolumeReclaimPolicy': 'Retain',
				'capacity': {
					'storage': volume_size
				},
				'volumeMode': volumeMode,
				'storageClassName': sc_name,
				'csi': {
					'driver': 'nvmesh-csi.excelero.com',
					'volumeHandle': nvmesh_volume_name
				}
			}
		}

	@staticmethod
	def delete_all_testing_pv():
		pv_list = core_api.list_persistent_volume(label_selector=TEST_LABEL_KEY)
		for pv in pv_list.items:
			KubeUtils.delete_pv(pv.metadata.name)

	@staticmethod
	def delete_pv(pv_name):
		return core_api.delete_persistent_volume(pv_name)

	@staticmethod
	def wait_for_pv_to_be_released(pv_name):
		KubeUtils.wait_for_pv_status(pv_name, expected_status='Released')

	@staticmethod
	def wait_for_pv_status(pv_name, expected_status, attempts=60):
		status = None
		pv = None
		while attempts > 0:
			pv = KubeUtils.get_pv_by_name(pv_name)
			if pv:
				status = pv.status.phase
				if status == expected_status:
					logger.info('PV {} is {}'.format(pv_name, expected_status))
					return
			logger.debug('Waiting for pv {} to be {}, current status: {}'.format(pv_name, expected_status, status))
			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pv {} to be {}, current status: {}, reason: {}'.format(pv_name, expected_status, status, pv.status.reason))

	@staticmethod
	def wait_for_pv_to_delete(pv_name, attempts=60):
		while attempts > 0:
			try:
				pv = KubeUtils.get_pv_by_name(pv_name)
				if pv:
					logger.debug('Waiting for pv {} to delete'.format(pv_name))
				else:
					raise ApiException()
			except ApiException as ex:
				logger.debug('pv {} deleted'.format(pv_name))
				return
			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for pv {} to delete'.format(pv_name))

	@staticmethod
	def get_node_by_name(node_name):
		field_selector = 'metadata.name={}'.format(node_name)
		nodes = core_api.list_node(field_selector=field_selector)

		for node in nodes.items:
			if node.metadata.name == node_name:
				return node

	@staticmethod
	def get_all_nodes():
		nodes = core_api.list_node()
		return nodes.items

	@staticmethod
	def get_nodes_per_zone(zone):
		label_selector = 'nvmesh-csi.excelero.com/zone={}'.format(zone)
		nodes = core_api.list_node(label_selector=label_selector)

		return nodes.items

	@staticmethod
	def get_zone_from_node(node):
		return node.metadata.labels['nvmesh-csi.excelero.com/zone']

	@staticmethod
	def get_all_node_names_by_zone():
		all_nodes = KubeUtils.get_all_nodes()
		zones = {}
		for node in all_nodes:
			zone = node.metadata.labels.get(consts.TopologyKey.ZONE, 'not-in-nvmesh-zone')
			if not zone in zones:
				zones[zone] = []

			zones[zone].append(node.metadata.name)
		return zones

	@staticmethod
	def get_test_labels():
		labels = {
			TEST_LABEL_KEY: '',
		}

		return labels


class NVMeshUtils(object):
	@staticmethod
	def delete_all_nvmesh_volumes(mgmt_addresses=None):
		if not mgmt_addresses:
			mgmt_addresses = TestConfig.ManagementServers

		for mgmt_address in mgmt_addresses:
			projection = [MongoObj(field='_id', value=1)]
			err, volume_list = VolumeAPI(managementServers=mgmt_address).get(projection=projection)
			if len(volume_list) != 0:
				err, out = VolumeAPI(managementServers=mgmt_address).delete([ vol._id for vol in volume_list ])
				if err:
					raise TestError('Failed to delete NVMesh volumes. Error: {}'.format(err))

				for vol_res in out:
					if not vol_res['success']:
						if 'Couldn\'t find the specified volume' not in vol_res['error']:
							raise TestError('Failed to delete NVMesh volume {}. Error: {}'.format(vol_res['_id'], vol_res['error']))

	@staticmethod
	def getVolumeAPI(mgmt_address=TestConfig.ManagementServers[0]):
		return VolumeAPI(managementServers=mgmt_address)

	@staticmethod
	def csi_id_to_nvmesh_name(co_vol_name):
		# Nvmesh vol name / id cannot be longer than 23 characters
		return 'csi-' + co_vol_name[4:22]

	@staticmethod
	def get_nvmesh_volume_by_name(nvmesh_vol_name, mgmt_addresses=None):
		if not mgmt_addresses:
			mgmt_addresses = TestConfig.ManagementServers

		for mgmt_address in mgmt_addresses:
			filter_obj = [MongoObj(field='_id', value=nvmesh_vol_name)]
			err, out = VolumeAPI(managementServers=mgmt_address).get(filter=filter_obj)
			if len(out) > 0:
				return out[0], mgmt_address

		return None, None

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
	def wait_for_nvmesh_volume(nvmesh_vol_name, attempts=15):
		while attempts > 0:
			volume, mgmt_address = NVMeshUtils.get_nvmesh_volume_by_name(nvmesh_vol_name)
			if not volume:
				logger.info('Waiting for NVMesh Volume {} to be created'.format(nvmesh_vol_name))
			else:
				logger.info('NVMesh Volume {} created'.format(nvmesh_vol_name))
				return mgmt_address

			attempts = attempts - 1
			time.sleep(1)

		raise TestError('Timed out waiting for NVMesh Volume {} to be created'.format(nvmesh_vol_name))

	@staticmethod
	def wait_for_nvmesh_vol_properties(nvmesh_vol_name, params, unittest_instance, attempts=1):
		while attempts:
			attempts = attempts - 1
			volume, mgmt_address = NVMeshUtils.get_nvmesh_volume_by_name(nvmesh_vol_name)

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
						key=nvmesh_key, val=nvmesh_value, expected_val=expected_val))
					if not attempts:
						unittest_instance.assertEqual(str(expected_val).lower(), str(nvmesh_value).lower(), 'Wrong value in Volume {}'.format(nvmesh_key))
				else:
					return mgmt_address
			time.sleep(1)


class VolumeBindingMode(object):
	Immediate = 'Immediate'
	WaitForFirstConsumer = 'WaitForFirstConsumer'