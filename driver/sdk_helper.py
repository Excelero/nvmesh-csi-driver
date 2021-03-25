from driver.common import DriverLogger, Utils
from config import Config
from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.ConnectionManager import ManagementTimeout

class NVMeshSDKHelper(object):
	logger = DriverLogger("NVMeshSDKHelper")

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