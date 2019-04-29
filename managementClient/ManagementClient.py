import json
import os
import requests
import urllib3
import urlparse
from packaging import version

import Consts, LoggerUtils
from Consts import VolumeAttachmentStatus
from managementClient.unitConverter import convertUnitToBytes

urllib3.disable_warnings()
class ManagementClientError(Exception):
	pass

class ManagementTimeout(ManagementClientError):
	def __init__(self, iport, msg=''):
		ManagementClientError.__init__(self, 'Could not connect to Management at {0}'.format(iport), msg)

class ManagementLoginFailed(ManagementClientError):
	def __init__(self, iport, msg=''):
		ManagementClientError.__init__(self, 'Could not login to Management at {0}'.format(iport), msg)

class ManagementClientHTTPError(ManagementClientError):
	def __init__(self, res):
		self.status_code = res.status_code
		self.message = "Reason:{0} Content:{1}".format(res.reason, res.content)

class ManagementClient(object):
	DEFAULT_USERNAME = "app@excelero.com"
	DEFAULT_PASSWORD = "admin"
	DEFAULT_NVMESH_CONFIG_FILE = '/etc/opt/NVMesh/nvmesh.conf'

	def __init__(self, managementServer=None, user=DEFAULT_USERNAME, password=DEFAULT_PASSWORD, configFile=DEFAULT_NVMESH_CONFIG_FILE):
		self.managementServer = None
		self.configFile = configFile
		self.setManagementServer(managementServer)
		self.user = user
		self.password = password
		self.logger = LoggerUtils.getInfraClientLogger('ManagementClient')
		self.session = requests.session()
		self.isAlive()

	def login(self):
		try:
			self.session.post("{}/login".format(self.managementServer), params={"username": self.user, "password": self.password}, verify=False)
		except requests.ConnectionError as ex:
			raise ManagementTimeout(self.managementServer, ex.message)

	def getVersion(self):
		err, out = self.get('/version')
		commitRecords = str(out).split()
		dictObject = {}
		for record in commitRecords:
			dictObject[(record.split('='))[0]] = (record.split('='))[1]
		return err, dictObject

	def isVersionEqualOrHigher(self, versionPrefix):
		# versionPrefix must be of type '[0-9]+(.[0-9])*', i.e. '1.2.1' or '2'
		err, dict = self.getVersion()
		currentVersion = dict.get('version')
		if currentVersion:
			currentVersion = currentVersion.replace('"','').replace('v', '') # omit double quotes
			currentVersion = currentVersion.split('-')[0]
			return version.parse(currentVersion) >= version.parse(versionPrefix)

		# in 1.2 we don't have the version in the dictionary
		return False

	def isAlive(self):
		try:
			err, out = self.get('/isAlive')
			return True if not err else False
		except ManagementTimeout as ex:
			return False

	def getDiskByID(self, diskID):
			err, out = self.get('/disks/{}'.format(diskID))
			return err, out

	def getModels(self):
		err, out = self.get('/disks/models')
		return err, out

	def getDisksByModel(self, model):
		err, out = self.get('/disks/disksByModel/{}'.format(model))
		return err, out

	def getNodes(self, nodeType, page=0, count=0, filterObject=None, sortObject=None, projectionObject=None):
		filterObject = {} if not filterObject else filterObject
		sortObject = {} if not sortObject else sortObject
		projectionObject = {} if not projectionObject else projectionObject
		data = {
			'filter': json.dumps(filterObject),
			'sort': json.dumps(sortObject),
			'projection': json.dumps(projectionObject)
		}
		err, out = self.get('/{0}/all/{1}/{2}/'.format(nodeType, page, count), data)

		return err, out

	def getServers(self, page=0, count=0, filterObject=None, sortObject=None, projectionObject=None):
		return self.getNodes(nodeType='servers', page=page, count=count, filterObject=filterObject, sortObject=sortObject, projectionObject=projectionObject)

	def getClients(self, page=0, count=0, filterObject=None, sortObject=None, projectionObject=None):
		return self.getNodes(nodeType='clients', page=page, count=count, filterObject=filterObject, sortObject=sortObject, projectionObject=projectionObject)

	def getServersCount(self, filterObject={}):
		err, out = self.get('/servers/count/?filter={0}'.format(json.dumps(filterObject)))

		return err, out

	def getClientsCount(self, filterObject={}):
		err, out = self.get('/clients/count/?filter={0}'.format(json.dumps(filterObject)))

		return err, out

	def getVolumes(self, page=0, count=0, filterObject=None, sortObject=None, projectionObject=None):
		filterObject     = {} if not filterObject else filterObject
		sortObject       = {} if not sortObject else sortObject
		projectionObject = {} if not projectionObject else projectionObject
		data = {
			'filter': json.dumps(filterObject),
			'sort': json.dumps(sortObject),
			'projection': json.dumps(projectionObject)
		}

		err, out = self.get('/volumes/all/{0}/{1}/'.format(page, count), data)

		return err, out

	def getVolumesIDs(self):
		err, out  = self.get('/volumes/ids')
		return err, out

	def getAttachVolumesPerClient(self, clientID, returnHidden=False):
		filterClient = '{{"client_id": "{}"}}'.format(clientID)
		err, out = self.get('/clients/all/0/0?filter={}'.format(filterClient))
		attachedVolumes = []
		found = False
		if not err:
			for client in out:
				if client["client_id"] == clientID:
					attachedVolumes = [volume for volume in client["block_devices"] if volume['vol_status'] in [VolumeAttachmentStatus.DETACH_FAILED, VolumeAttachmentStatus.ATTACHED, VolumeAttachmentStatus.BUSY]]

					if not returnHidden:
						attachedVolumes = [volume for volume in attachedVolumes if 'is_hidden' not in volume or ('is_hidden' in volume and not volume['is_hidden'])]

					attachedVolumes = [volume["name"] for volume in attachedVolumes]
					found = True
					break

			if not found:
				err = "Client {} was not found on management".format(clientID)
				self.logger.warning(err)
				return err, None

		return err, attachedVolumes

	def getVolumeStats(self, volumeName, limit=10):
		url = '/volumes/stats/{0}/{1}'.format(volumeName, limit)

		err, jsonObj = self.get(url)

		return err, jsonObj

	def getVolumeDailyStats(self, volumeName, client=None, lastHours=10):
		url = '/volumes/getDailyStatistics/'
		url += '{0}/{1}/{2}'.format(client, volumeName, lastHours) if client else '{0}/{1}'.format(volumeName, lastHours)

		err, jsonObj = self.get(url)

		return err, jsonObj

	def getDiskStats(self, diskID, limit=10):
		url = '/servers/diskStats/{0}/{1}'.format(diskID, limit)

		err, jsonObj = self.get(url)

		return err, jsonObj

	def getDiskDailyStats(self, diskID, lastHours=10):
		url = '/disks/getDailyStatistics/{0}/{1}'.format(diskID, lastHours)

		err, jsonObj = self.get(url)

		return err, jsonObj

	def getVolumeByName(self, name):
		url = '/volumes/all/0/0?filter={{"_id" : "{0}"}}'.format(name)
		err, jsonObj = self.get(url)

		if err:
			return err, None

		out = None

		if len(jsonObj) != 0:
			out = jsonObj[0]
		else:
			err = "Volume {} not found!".format(name)

		return err, out

	def getVolumesByNames(self, namesList):

		url = '/volumes/all/0/0?filter={{"_id" : {{"$in":{0} }}}}'.format(json.dumps(namesList))
		err, jsonObj = self.get(url)

		if err:
			return err, None

		return err, jsonObj

	def createVolumeVpgPayload(self, arguments):
		payload = {
			'name': arguments['volume'] if 'volume' in arguments else arguments['name'],
		}

		if 'description' in arguments:
			payload['description'] = arguments['description']

		if 'diskClasses' in arguments:
			payload['diskClasses'] = arguments['diskClasses']

		if 'serverClasses' in arguments:
			payload['serverClasses'] = arguments['serverClasses']

		if 'domain' in arguments:
			payload['domain'] = arguments['domain']

		if 'RAIDLevel' in arguments:
			payload['RAIDLevel'] = arguments['RAIDLevel']

			if arguments['RAIDLevel'] == Consts.RAIDLevels.RAID0:
				payload['stripeSize'] = arguments['stripeSize']
				payload['stripeWidth'] = arguments['stripeWidth']

			elif arguments['RAIDLevel'] == Consts.RAIDLevels.RAID1:
				payload['numberOfMirrors'] = arguments['numberOfMirrors'] if 'numberOfMirrors' in arguments else 1

			elif arguments['RAIDLevel'] == Consts.RAIDLevels.RAID10:
				payload['stripeSize'] = arguments['stripeSize']
				payload['stripeWidth'] = arguments['stripeWidth']
				payload['numberOfMirrors'] = arguments['numberOfMirrors']

			elif arguments['RAIDLevel'] == Consts.RAIDLevels.ERASURE_CODING:
				payload['dataBlocks'] = arguments['dataBlocks']
				payload['stripeWidth'] = 1
				payload['stripeSize'] = arguments['stripeSize']
				payload['protectionLevel'] = arguments['protectionLevel']
				payload['parityBlocks'] = arguments['parityBlocks']

			elif arguments['RAIDLevel'] != Consts.RAIDLevels.LVM_JBOD and arguments['RAIDLevel'] != Consts.RAIDLevels.CONCATENATED:
				msg = 'Unknown RAIDLevel: {0}'.format(arguments['RAIDLevel'])
				self.logger.error(msg)
				raise ValueError(msg)

		if 'volume' in arguments:
			payload['capacity'] = 'MAX' if str(arguments['capacity']).upper() == 'MAX' else convertUnitToBytes(arguments['capacity'])

			if 'limitByNodes' in arguments:
				payload['limitByNodes'] = arguments['limitByNodes']

			if 'limitByDisks' in arguments:
				payload['limitByDisks'] = arguments['limitByDisks']

			if 'VPG' in arguments:
				payload['VPG'] = arguments['VPG']

		else:
			if 'capacity' in arguments:
				self.logger.debug('capacity = %s' % arguments['capacity'])
				payload['capacity'] = convertUnitToBytes(arguments['capacity'])


		return payload

	def createVolume(self, arguments):
		volumePayload = {}
		payload = self.createVolumeVpgPayload(arguments)
		volumePayload['create'] = [payload]
		volumePayload['remove'] = []
		volumePayload['edit'] = []
		err, out = self.post("/volumes/save", volumePayload)

		self.logger.info(json.dumps(volumePayload))
		return err, out

	def removeVolumesByIds(self, ids):
		payload = {'remove': [{'_id': id} for id in ids]}
		err, out = self.post("/volumes/save", payload)

		return err, out

	def removeVolume(self, arguments):
		volumePayload = {'create': [], 'remove': [arguments], 'edit': []}
		err, out = self.post("/volumes/save", volumePayload)

		for line in volumePayload:
			self.logger.info(volumePayload[line])

		return err, out

	def editVolume(self, arguments, autoCompleteFields=True):
		volumePayload = {}
		if autoCompleteFields:
			err, payload = self.getVolumeByName(arguments['volume'])
			if err:
				return err, None

			if 'capacity' in arguments.keys():
				if arguments['capacity'] == "MAX":
					payload['capacity'] = arguments['capacity']
				else:
					payload['capacity'] = convertUnitToBytes(arguments['capacity'])
			if 'description' in arguments.keys():
				payload['description'] = arguments['description']
			if 'discClasses' in arguments.keys():
				payload['discClasses'] = arguments['discClasses']
		else:
			payload = arguments

		volumePayload['edit'] = [payload]
		err, out = self.post("/volumes/save", volumePayload)
		return err, out

	def setControlJobs(self, arguments, job):
		client = {
			'_id': arguments['client'],
			'controlJobs': [{'uuid': volume, 'control': job} for volume in arguments['volumes']]
		}
		self.logger.info(json.dumps(client))

		err, out = self.post('/clients/update', [client])

		return err, out

	def attachVolumes(self, arguments):
		return self.setControlJobs(arguments, Consts.ControlJobs.TO_BE_ATTACHED)

	def detachVolumes(self, arguments):
		return self.setControlJobs(arguments, Consts.ControlJobs.TO_BE_DETACHED)

	def getDriveClasses(self, filterObj={}, sortObj={}):
		err, out = self.get('/diskClasses/all?filter={}&sort={}'.format(json.dumps(filterObj), json.dumps(sortObj)))
		return err, out

	def createDriveClasses(self, arguments):
		drivesArray = arguments['disks']
		driveClassesPayload = {
			'disks': drivesArray,
			'_id'  : arguments['_id'],
		}

		if 'description' in arguments.keys():
			driveClassesPayload['description'] = arguments['description']

		if 'domains' in arguments.keys():
			driveClassesPayload['domains'] = arguments['domains']

		err, out = self.post('/diskClasses/save', [driveClassesPayload])
		return err, out

	def deleteDriveClasses(self, arguments):
		objId = arguments['_id']
		driveClassesPayload = {'_id': objId}
		err, out = self.post('/diskClasses/delete', [driveClassesPayload])
		return err, out

	def updateDriveClasses(self, arguments):
		driveClassesPayload = {'_id': arguments['_id']}

		if 'disks' in arguments.keys():
			driveClassesPayload['disks'] = arguments['disks']

		if 'description' in arguments.keys():
			driveClassesPayload['description'] = arguments['description']

		if 'domains' in arguments.keys():
			driveClassesPayload['domains'] = arguments['domains']

		err, out = self.post('/diskClasses/update', [driveClassesPayload])
		return err, out

	def getTargetClasses(self, filterObj={}, sortObj={}):
		err, out = self.get('/serverClasses/all?filter={}&sort={}'.format(json.dumps(filterObj), json.dumps(sortObj)))
		return err, out

	def createTargetClasses(self, arguments):
		targetsArray = arguments['targetNodes']
		targetClassesPayload = {
			'targetNodes': targetsArray,
			'name': arguments['name'],
		}

		if 'description' in arguments.keys():
			targetClassesPayload['description'] = arguments['description']

		if 'domains' in arguments.keys():
			targetClassesPayload['domains'] = arguments['domains']

		err, out = self.post('/serverClasses/save', [targetClassesPayload])
		return err, out

	def deleteTargetClasses(self, arguments):
		objId = arguments['_id']
		targetClassesPayload = {'_id': objId}
		err, out = self.post('/serverClasses/delete', [targetClassesPayload])
		return err, out

	def updateTargetClasses(self, arguments):
		targetClassesPayload = {'_id': arguments['_id']}

		if 'targetNodes' in arguments.keys():
			targetClassesPayload['targetNodes'] = arguments['targetNodes']

		if 'description' in arguments.keys():
			targetClassesPayload['description'] = arguments['description']

		if 'domains' in arguments.keys():
			targetClassesPayload['domains'] = arguments['domains']

		err, out = self.post('/serverClasses/update', [targetClassesPayload])
		return err, out

	def getVpgs(self, filterObj=None, sortObj=None):
		filterObj = {} if not filterObj else filterObj
		sortObj = {} if not sortObj else sortObj
		err, out = self.get('/volumeProvisioningGroups/all?filter={}&sort={}'.format(
				json.dumps(filterObj), json.dumps(sortObj)))

		return err, out

	def createVPGs(self, arguments):
		payload = self.createVolumeVpgPayload(arguments)

		err, out = self.post('/volumeProvisioningGroups/save', [payload])
		return err, out

	def deleteVpgs(self, arguments):
		objId = arguments['_id']
		vpgsPayload = {'_id': objId}
		err, out = self.post('/volumeProvisioningGroups/delete', [vpgsPayload])
		return err, out

	def _evictDriveVer1_2(self, arguments):
		evictPayload = []
		for diskID in arguments['diskIDs']:
			payload = {'diskID': diskID}
			evictPayload.append(payload)

		err, out = self.post('/servers/evictDiskByDiskIds', evictPayload)
		return err, out

	def evictDrive(self, arguments):
		if not self.isVersionEqualOrHigher('1.3.0'):
			return self._evictDriveVer1_2(arguments)
		evictList = []
		for diskID in arguments['diskIDs']:
			evictList.append(diskID)
		evictPayload = {}
		evictPayload["Ids"] = evictList
		err, out = self.post('/disks/evictDiskByDiskIds', evictPayload)
		return err, out

	def _deleteDriveByIDVer1_2(self, driveId):
		err, out = self.post('/disks/delete/{}'.format(driveId))
		return err, out

	def deleteDriveByID(self, driveId):
		if not self.isVersionEqualOrHigher('1.3.0'):
			return self._deleteDriveByIDVer1_2(driveId)
		# currently the test supports only one drive ID to delete
		# so for now ignoring the ability of the REST API to delete a list of drives
		payload = {}
		drivesToRemove = []
		drivesToRemove.append(driveId)
		payload["Ids"] = drivesToRemove
		err, out = self.post('/disks/delete', payload)
		return err, out

	def rebuildVolume(self, volumeIds):
		err, out = self.post("/volumes/rebuildVolumes", volumeIds)
		return err, out

	def countClients(self):
		err, out = self.get('/clients/count')
		return err, out

	def deleteServers(self, arguments):
		err, out = self.post('/servers/delete', arguments)
		return err, out

	def deleteClients(self, arguments):
		err, out = self.post('/clients/delete', arguments)
		return err, out

	def updateClients(self, arguments):
		err, out = self.post('/clients/update', arguments)
		return err, out

	def updateTargets(self, arguments):
		err, out = self.post('/servers/update', arguments)
		return err, out

	def setTargetsBatchControlJobs(self, arguments):
		err, out = self.post('/servers/setBatchControlJobs', arguments)
		return err, out

	def changePassword(self, user, password, confirmationPassword):
		payload = {
			'_id': user,
			'password': password,
			'confirmationPassword': confirmationPassword
		}
		err, out = self.post('/users/changePassword', payload)
		return err, out

	def getHaPeersStatus(self):
		err, out = self.get('/managementCluster/all/0/0')
		return err, out

	def getDiskCapabilities(self, diskId):
		err, out = self.getDiskByID(diskId)
		payload = {}
		if not err and 'disks' in out:
			disk = out['disks']
			payload['status'] = disk['status']
			payload['Vendor'] = disk['Vendor']
			payload['reappearingCounter'] = disk['reappearingCounter'] if 'reappearingCounter' in disk else 0
			payload['metadata_size'] = disk['metadata_size'] if 'metadata_size' in disk and disk['metadata_size'] is not None else 0
			payload['writeCounter'] = disk['writeCounter'] if 'writeCounter' in disk and disk['writeCounter'] is not None else -1
			payload['formatRequestCounter'] = disk['formatRequestCounter'] if 'formatRequestCounter' in disk else 0
			payload['activeFormatRequestCounter'] = disk['activeFormatRequestCounter'] if 'activeFormatRequestCounter' in disk else 0
			payload['isOutOfService'] = disk['isOutOfService'] if 'isOutOfService' in disk else False
			payload['automaticallyEvicted'] = disk['automaticallyEvicted'] if 'automaticallyEvicted' in disk else False
			payload['isPendingFormat'] = disk['isPendingFormat'] if 'isPendingFormat' in disk else False
			payload['formatInProgress'] = disk['formatInProgress'] if 'formatInProgress' in disk else False
			payload['metadataCapabilities'] = disk['metadataCapabilities'] if 'metadataCapabilities' in disk else []
			payload['formatDetails'] = disk['formatDetails'] if 'formatDetails' in disk else None
			payload['formatOptions'] = disk['formatOptions'] if 'formatOptions' in disk else []

		return err, payload

	def _formatDiskUrl(self):
		if self.isVersionEqualOrHigher('1.3.0'):
			return '/disks/formatDiskByDiskIds'
		return '/servers/formatDiskByDiskIds'

	def formatDisk(self, arguments):
		payload = {}
		payload['formatType'] = arguments['formatType']
		payload['diskIDs'] = [diskID for diskID in arguments['diskIDs']]

		return self.post(self._formatDiskUrl(), payload)

	def post(self, route, payload=None):
		return self.request('post', route, payload)

	def get(self, route, payload=None):
		return self.request('get', route, payload)

	def request(self, method, route, payload=None, numberOfRetries = 0):
		# self.logger.debug("request method={0} route={1} payload={2} retries={3}".format(method, route, payload, numberOfRetries))
		for i in range(len(self.managementServers)):
			self.managementServer = self.managementServers[0]
			try:
				return self.do_request(method, route, payload, numberOfRetries)
			except ManagementTimeout as ex:
				# put it as last
				self.managementServers.append(self.managementServers.pop(0))

		raise ManagementTimeout(route, "Timeout from all Management Servers ({})".format(', '.join(self.managementServers)))

	def do_request(self, method, route, payload=None, numberOfRetries=0):
		res = None
		if route != '/isAlive':
			self.logger.debug('request method={0} route={1} payload={2} retries={3}'.format(method, route, payload, numberOfRetries))
		url = ''
		try:
			url = urlparse.urljoin(self.managementServer, route)
			if method == 'post':
				res = self.session.post(url, json=payload, verify=False)
			elif method == 'get':
				res = self.session.get(url, params=payload, verify=False)

			if '/login' in res.text:
				self.login()
				numberOfRetries += 1
				if numberOfRetries < 3:
					return self.request(method, route, payload, numberOfRetries)
				else:
					raise ManagementLoginFailed(iport=url)

		except requests.ConnectionError as ex:
			numberOfRetries += 1
			if numberOfRetries < 3:
				return self.request(method, route, payload, numberOfRetries)
			else:
				raise ManagementTimeout(url, ex.message)

		jsonObj = None
		err = None

		if route != '/isAlive':
			self.logger.debug('route {0} got response: {1}'.format(route, res.content))

		if res.status_code in [200, 304]:
			try:
				if res.content:
					jsonObj = json.loads(res.content)
			except Exception as ex:
				err = {
					"code": res.status_code,
					"message": ex.message,
					"content": res.content
				}
		else:
			err = {
				"code": res.status_code,
				"message": res.reason,
				"content": res.content
			}

		return err, jsonObj

	def managementReadConfig(self):
		g = {}
		l = {}

		if os.path.exists(self.configFile):
			execfile(self.configFile , g, l)

		if 'MANAGEMENT_PROTOCOL' in l:
			protocol = l['MANAGEMENT_PROTOCOL']
		else:
			raise Exception('MANAGEMENT_PROTOCOL variable could not be found in: {0}'.format(self.configFile))

		if 'MANAGEMENT_SERVERS' in l:
			servers=l['MANAGEMENT_SERVERS'].replace('4001', '4000').split(',')
		else:
			raise Exception('MANAGEMENT_SERVERS variable could not be found in: {0}'.format(self.configFile))

		self.managementServers = []
		for server in servers:
			self.managementServers = self.managementServers + [protocol + '://' + server]

		return self.managementServers

	def setManagementServer(self, managementServers=None):
		if managementServers:
			if isinstance(managementServers, list):
				self.managementServers = managementServers
			else:
				self.managementServers = [managementServers]
		else:
			self.managementReadConfig()
