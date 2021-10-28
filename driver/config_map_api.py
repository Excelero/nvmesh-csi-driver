import logging
import os

from kubernetes import client, config, watch as client_watch
from kubernetes.client.rest import ApiException

from config import Config

namespace = ''
core_api = None

def init():
	global core_api
	global namespace

	if core_api:
		return

	if os.environ.get('DEVELOPMENT'):
		config.load_kube_config()
		namespace = 'nvmesh-csi-driver'
		configuration = client.Configuration()
		configuration.verify_ssl = False
		configuration.debug = False
		client.Configuration.set_default(configuration)
		core_api = client.CoreV1Api()
	else:
		config.load_incluster_config()
		namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
		core_api = client.CoreV1Api()

	kube_logger = logging.getLogger('kubernetes')
	kube_logger.setLevel(logging.getLevelName(Config.KUBE_CLIENT_LOG_LEVEL or 'DEBUG'))

class ConfigMapNotFound(Exception):
	pass

class ConfigMapAlreadyExists(Exception):
	pass

def load(config_map_name):
	config_maps = core_api.list_namespaced_config_map(namespace, field_selector='metadata.name=%s' % config_map_name)
	if len(config_maps.items):
		return config_maps.items[0]
	else:
		raise ConfigMapNotFound('Could not find ConfigMap {} in namespace {}'.format(config_map_name, namespace))

def update(config_map_name, data):
	body = {
		"data": data
	}

	try:
		api_response = core_api.patch_namespaced_config_map(config_map_name, namespace, body)
		return api_response
	except ApiException as e:
		if e.reason == 'Not Found':
			raise ConfigMapNotFound('Could not find ConfigMap {} in namespace {}'.format(config_map_name, namespace))
		else:
			raise

def create(config_map_name, data):
	body = {
		"metadata": {
			"name": config_map_name
		},
		"data": data
	}

	try:
		api_response = core_api.create_namespaced_config_map(namespace, body)
		return api_response
	except ApiException as e:
		if e.reason == 'AlreadyExists':
			raise ConfigMapAlreadyExists(e.message)
		raise

def delete(config_map_name):
	try:
		api_response = core_api.delete_namespaced_config_map(config_map_name, namespace)
		return api_response
	except ApiException as e:
		raise

def watch(config_map_name, **kwargs):
	core_api = client.CoreV1Api()
	watcher = client_watch.Watch()
	stream = watcher.stream(core_api.list_namespaced_config_map, namespace=namespace, field_selector='metadata.name=%s' % config_map_name, **kwargs)
	return stream, watcher
