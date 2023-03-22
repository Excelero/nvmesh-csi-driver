import logging
import threading

from NVMeshSDK.APIs.ClientAPI import ClientAPI
from NVMeshSDK.MongoObj import MongoObj
from common import Utils
from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.ConnectionManager import ManagementTimeout
from config import Config

logger = logging.getLogger("NVMeshSDKHelper")

class NVMeshSDKHelper(object):

	@staticmethod
	def _try_to_connect_to_single_management():
		protocol = Config.MANAGEMENT_PROTOCOL
		managementServers = Config.MANAGEMENT_SERVERS
		user = Config.MANAGEMENT_USERNAME
		password = Config.MANAGEMENT_PASSWORD

		# This call will try to connect to the Management Server Instance
		api = VolumeAPI(managementServers=managementServers, managementProtocol=protocol, user=user, password=password, logger=logger)
		err, connected = api.managementConnection.get('/isAlive')

		if err:
			raise ValueError(err)

		return api, connected

	@staticmethod
	def init_session_with_single_management(stop_event):
		connected = False
		retries = 3
		api = None
		# try until able to connect to NVMesh Management
		print("Looking for NVMesh Management server using {} from servers {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
		while not connected and retries > 0:
			try:
				api, connected = NVMeshSDKHelper._try_to_connect_to_single_management()
				return api
			except ManagementTimeout as ex:
				logger.info("Waiting for NVMesh Management servers on ({}) {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
				stop_event.wait(10)
				
				retries = retries - 1
				
				if retries == 0:
					raise ex
			print("Connected to NVMesh Management server on ({}) {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))

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
	def get_client_api(api_params):
		try:
			client_api = ClientAPI(**api_params)
			return client_api
		except Exception as ex:
			logger.error('Failed to create ClientAPI with params: {}. \nError {}'.format(api_params, ex))
			raise
