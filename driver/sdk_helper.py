from driver import consts
from driver.common import DriverLogger, Utils
from config import Config
from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.ConnectionManager import ManagementTimeout
from driver.config import Config
from driver.topology import TopologyUtils


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

	@staticmethod
	def get_api_params_from_config():
		return {
			'managementServers': Config.MANAGEMENT_SERVERS,
			'managementProtocol': Config.MANAGEMENT_PROTOCOL,
			'user': Config.MANAGEMENT_USERNAME,
			'password': Config.MANAGEMENT_PASSWORD
		}

	@staticmethod
	def get_api_params(logger, zone):
		if Config.TOPOLOGY_TYPE == consts.TopologyType.SINGLE_ZONE_CLUSTER:
			return NVMeshSDKHelper.get_api_params_from_config()

		mgmt_info = TopologyUtils.get_management_info_from_zone(zone)

		if not mgmt_info:
			raise ValueError('Missing "management" key in Config.topology.zones.%s' % zone)

		managementServers = mgmt_info.get('servers')
		if not managementServers:
			raise ValueError('Missing "servers" key in Config.topology.zones.%s.management ' % zone)

		api_params = {
			'managementServers': managementServers
		}

		user = mgmt_info.get('user')
		password = mgmt_info.get('password')
		protocol = mgmt_info.get('protocol')

		if user:
			api_params['user'] = user

		if password:
			api_params['password'] = password

		if protocol:
			api_params['protocol'] = protocol

		logger.debug('Topology zone {} management params:  is {}'.format(zone, api_params))
		return api_params

	@staticmethod
	def get_volume_api(logger, zone=None):
		api_params = NVMeshSDKHelper.get_api_params(logger, zone)

		try:
			volume_api = VolumeAPI(logger=logger.getChild('NVMeshSDK'), **api_params)
			return volume_api
		except Exception as ex:
			logger.error('Failed to create VolumeAPI with params: {}. \nError {}'.format(api_params, ex))
			raise