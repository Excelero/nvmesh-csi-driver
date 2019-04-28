import urllib3
from managementClient.ManagementClient import ManagementClient
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ManagementClientWrapper(ManagementClient):
	def attachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.attachVolumes(requestObj)

	def detachVolume(self, volumeID, nodeID):
		requestObj = {"client": nodeID, "volumes": [ volumeID ] }
		return self.detachVolumes(requestObj)