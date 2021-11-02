from kubernetes.client.rest import ApiException

from driver import config_map_api


class ConfigMapMockedItem(object):
	def __init__(self, json_body):
		self._raw_body = json_body
		self.data = json_body['data']

class ConfigMapMockedList(object):
	def __init__(self, items):
		self.items = items

class K8sConfigMapMockAPI(object):
	def __init__(self):
		self._objects = {}

	def _get_namespaced_name(self, namespace, name):
		return namespace + '_' + name

	def list_namespaced_config_map(self, namespace, field_selector=None):
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
		namespaced_name = self._get_namespaced_name(namespace, config_map_name)
		if namespaced_name not in self._objects:
			raise ApiException('Not Found', reason='Not Found')
		self._objects[namespaced_name] = ConfigMapMockedItem(body)

	def create_namespaced_config_map(self, namespace, body):
		namespaced_name = self._get_namespaced_name(namespace, body['metadata']['name'])
		new_config_map = ConfigMapMockedItem(body)
		self._objects[namespaced_name] = new_config_map
		return new_config_map

	def delete_namespaced_config_map(self, config_map_name, namespace):
		namespaced_name = self._get_namespaced_name(namespace, config_map_name)
		if namespaced_name not in self._objects:
			ApiException('Not Found', reason='Not Found')
		self._objects.pop(namespaced_name)

	# TODO (Tests): mock watch on the watch client ..

# This will replace the k8s client for config_map_api module to simulate it's behavior without the need of an actual kubernetes cluster

def init_mocked_api():
	config_map_api.core_api = K8sConfigMapMockAPI()
