import logging
import threading

from NVMeshSDK.APIs.ClientAPI import ClientAPI
from NVMeshSDK.MongoObj import MongoObj
from common import Utils
from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.ConnectionManager import ManagementTimeout
from config import Config


class NVMeshSDKHelper(object):
	logger = logging.getLogger("NVMeshSDKHelper")

	@staticmethod
	def _try_to_connect_to_single_management(logger):
		protocol = Config.MANAGEMENT_PROTOCOL
		managementServers = Config.MANAGEMENT_SERVERS
		user = Config.MANAGEMENT_USERNAME
		password = Config.MANAGEMENT_PASSWORD

		# This call will try to connect to the Management Server Instance
		api = VolumeAPI(managementServers=managementServers, managementProtocol=protocol, user=user, password=password, logger=logger)
		err, connected = api.managementConnection.get('/isAlive')

		if err:
			raise err

		return api, connected

	@staticmethod
	def init_session_with_single_management(logger):
		connected = False
		api = None
		# try until able to connect to NVMesh Management
		print("Looking for a NVMesh Management server using {} from servers {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
		while not connected:
			try:
				api, connected = NVMeshSDKHelper._try_to_connect_to_single_management(logger)
			except ManagementTimeout as ex:
				NVMeshSDKHelper.logger.info("Waiting for NVMesh Management servers on ({}) {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
				Utils.interruptable_sleep(10)

			print("Connected to NVMesh Management server on ({}) {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
		return api

	@staticmethod
	def get_management_version(api):
		err, out = api.managementConnection.get('/version')
		if not err:
			version_info = {}
			lines = out.split('\n')
			for line in lines:
				try:
					key_val_pair = line.split('=')
					key = key_val_pair[0]
					value = key_val_pair[1].replace('"','')
					version_info[key] = value
				except:
					pass
			return version_info
		return None

	@staticmethod
	def get_client_api(logger, api_params):
		try:
			volume_api = ClientAPI(logger=logger.getChild('NVMeshSDK'), **api_params)
			return volume_api
		except Exception as ex:
			logger.error('Failed to create ClientAPI with params: {}. \nError {}'.format(api_params, ex))
			raise

	@staticmethod
	def check_if_node_in_management(node_name, api_params, logger):
		logger.debug('Checking if node {} is in management server: {}'.format(node_name, api_params))
		try:
			client_api = NVMeshSDKHelper.get_client_api(logger, api_params)
			filter_by_node_id=[MongoObj(field='_id', value=node_name)]
			err, res = client_api.get(filter=filter_by_node_id)
			if err:
				raise err

			return len(res) > 0 and res[0]._id == node_name
		except Exception as ex:
			logger.warning('Failed to check if node {} is in management {}. Error: {}'.format(node_name, api_params, ex))
			return False