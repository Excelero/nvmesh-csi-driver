import urllib3

from driver.config import Config
from managementClient.ManagementClient import ManagementClient
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ManagementClientWrapper(ManagementClient):
	def __init__(self, *args, **kwargs):

		if Config:
			protocol = Config.management.protocol or 'https'
			kwargs['managementServer'] = [ '{}://{}'.format(protocol, address) for address in Config.management.addresses ]

			if Config.management.credentials:
				kwargs['user'] = Config.management.credentials.username
				kwargs['password'] = Config.management.credentials.password

		ManagementClient.__init__(self, *args, **kwargs)

	def attachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.attachVolumes(requestObj)

	def detachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.detachVolumes(requestObj)