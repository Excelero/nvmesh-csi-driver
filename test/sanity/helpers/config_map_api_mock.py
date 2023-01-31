import json
from os import path
import os
from kubernetes.client.rest import ApiException

from driver import config_map_api
import logging
log = logging.getLogger('SanityTests')


#We save this to the disk so that the unittest can check the satate of the config-map (since the memory object is not accesible from there)
ON_DISK_CACHE_DIR = '/tmp/config_map_mocks/'

class ConfigMapMockedItem(object):
	def __init__(self, json_body):
		self._raw_body = json_body
		self.data = json_body['data']

class ConfigMapMockedList(object):
	def __init__(self, items):
		self.items = items

def read_config_map_from_disk(namespaced_name):
	config_map_file_name = path.join(ON_DISK_CACHE_DIR, namespaced_name)
	with open(config_map_file_name, 'r') as fp:
		return json.loads(fp.read())

class K8sConfigMapMockAPI(object):
	def __init__(self):
		self._objects = {}

	def save_to_disk(self):
		log.info("K8sConfigMapMockAPI::save_to_disk sdelf._objects=%s" % self._objects)
		for namespaced_name, config_map in self._objects.items():
			config_map_file_name = path.join(ON_DISK_CACHE_DIR, namespaced_name)
			with open(config_map_file_name, 'w') as fp:
				log.info("K8sConfigMapMockAPI::save_to_disk saving %s to %s - saving..."% (namespaced_name, config_map_file_name))
				fp.write(json.dumps(config_map.data))
				log.info("K8sConfigMapMockAPI::save_to_disk - finished")

	def _get_namespaced_name(self, namespace, name):
		return namespace + '_' + name

	def list_namespaced_config_map(self, namespace, field_selector=None):
		log.info("K8sConfigMapMockAPI::list_namespaced_config_map")
		selector = field_selector.split('=')
		if selector[0] == 'metadata.name':
			name = selector[1]
		else:
			raise ValueError('Expected field selector of metadata.name')

		namespaced_name = self._get_namespaced_name(namespace, name)
		config_map = self._objects.get(namespaced_name)
		if config_map:
			return ConfigMapMockedList([config_map])
		else:
			return ConfigMapMockedList([])

	def patch_namespaced_config_map(self, config_map_name, namespace, body):
		log.info("K8sConfigMapMockAPI::patch_namespaced_config_map")
		namespaced_name = self._get_namespaced_name(namespace, config_map_name)
		if namespaced_name not in self._objects:
			raise ApiException('Not Found', reason='Not Found')
		self._objects[namespaced_name] = ConfigMapMockedItem(body)
		self.save_to_disk()

	def create_namespaced_config_map(self, namespace, body):
		log.info("K8sConfigMapMockAPI::create_namespaced_config_map")
		namespaced_name = self._get_namespaced_name(namespace, body['metadata']['name'])
		new_config_map = ConfigMapMockedItem(body)
		self._objects[namespaced_name] = new_config_map
		self.save_to_disk()
		return new_config_map

	def delete_namespaced_config_map(self, config_map_name, namespace):
		log.info("K8sConfigMapMockAPI::delete_namespaced_config_map")
		namespaced_name = self._get_namespaced_name(namespace, config_map_name)
		if namespaced_name not in self._objects:
			ApiException('Not Found', reason='Not Found')
		self._objects.pop(namespaced_name)
		self.save_to_disk()

	# TODO (Tests): mock watch on the watch client ..

# This will replace the k8s client for config_map_api module to simulate it's behavior without the need of an actual kubernetes cluster

def init_mocked_api():
	config_map_api.namespace = 'nvmesh-csi'
	os.mkdir(ON_DISK_CACHE_DIR)
	config_map_api.core_api = K8sConfigMapMockAPI()
