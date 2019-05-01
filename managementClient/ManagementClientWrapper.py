import urllib3

from driver.config import Config
from managementClient.ManagementClient import ManagementClient
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ManagementClientWrapper(ManagementClient):
	def __init__(self, *args, **kwargs):
		protocol = Config.MANAGEMENT_PROTOCOL
		kwargs['managementServer'] = [ '{}://{}'.format(protocol, address.strip()) for address in Config.MANAGEMENT_SERVERS.split(',') ]
		kwargs['user'] = Config.MANAGEMENT_USERNAME
		kwargs['password'] = Config.MANAGEMENT_PASSWORD

		print("Initializing ManagementClient with managementServer={}".format(kwargs['managementServer']))
		# TODO: BUG - if managementServers are not available the ManagementClient.isAlive() hangs
		ManagementClient.__init__(self, *args, **kwargs)

	def attachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.attachVolumes(requestObj)

	def detachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.detachVolumes(requestObj)

	def createVolumeFromVpg(self, name, description, capacity, vpg):

		volume = {
			'name': name,
			'description': description,
			'capacity': capacity,
			'VPG': vpg
		}

		return self.createVolume(volume)