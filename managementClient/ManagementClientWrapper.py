import urllib3

import time

from driver.config import Config
from managementClient import Consts
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

	def createVolume(self, volume, wait_for_online=True):
		err, mgmtResponse = ManagementClient.createVolume(self, volume)

		if not wait_for_online or err:
			return err ,mgmtResponse

		createResult = mgmtResponse['create'][0]
		if not createResult['success']:
			return 'Could not create volume', createResult['err']

		return self._wait_for_volume_status(volume['name'], Consts.VolumeStatuses.ONLINE)

	def _wait_for_volume_status(self, volume_id, status):

		volume_status = None
		volume = None
		attempts = 15

		while volume_status != status:
			err, volume = self.getVolumeByName(volume_id)
			if err:
				return err, volume

			volume_status = volume['status']
			if volume_status == status:
				return None, volume

			attempts += 1
			time.sleep(1)

		return 'Timed out Waiting for Volume to be Online', volume

