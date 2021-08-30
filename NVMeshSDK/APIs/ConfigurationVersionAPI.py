from NVMeshSDK.Consts import EndpointRoutes
from NVMeshSDK.ConnectionManager import ConnectionManagerError, ConnectionManager
from NVMeshSDK.Utils import Utils


class ConfigurationVersionAPI(object):
	endpointRoute = EndpointRoutes.INDEX

	def __init__(self, managementServersUrls, logger=None):
		try:
			self.managementConnection = ConnectionManager.getInstance(managementServers=managementServersUrls, dbUUID=None, logger=logger)
		except ConnectionManagerError as e:
			raise e

	def getDBUUID(self):
		routes = ['dbUUID']

		err, response = self.makeGet(routes)

		if response is not None:
			ConnectionManager.addInstance(response['dbUUID'], self.managementConnection)
			return None, response
		else:
			return err, None

	def makeGet(self, routes):
		try:
			route = Utils.createRouteString(routes=routes, endPointRoute=self.getEndpointRoute())
			err, out = self.managementConnection.get(route)
			return err, out
		except ConnectionManagerError as e:
			raise e

	def save(self):
		raise NotImplemented

	def update(self):
		raise NotImplemented

	def delete(self):
		raise NotImplemented

	def count(self):
		raise NotImplemented

	@classmethod
	def getEndpointRoute(cls):
		return cls.endpointRoute
