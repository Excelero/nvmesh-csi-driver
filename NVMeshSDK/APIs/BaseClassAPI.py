"""
.. module:: BaseClassAPI
   :synopsis: All the base API functions are defined here
.. moduleauthor:: Excelero
"""
from NVMeshSDK.ConnectionManager import ConnectionManager, ConnectionManagerError
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Utils import Utils
from NVMeshSDK.LoggerUtils import Logger
from NVMeshSDK.APIs.ConfigurationVersionAPI import ConfigurationVersionAPI


class BaseClassAPI(object):
    configFile = '/etc/opt/NVMesh/nvmesh.conf'

    """All the base API functions are defined here."""
    def __init__(self, user=None, password=None, logger=None, managementServers=None, managementProtocol='https', dbUUID=None):
        """**Initializes a singleton connection to the management server, by default uses an application user,
        it is optional to provide a different user and password for the connection.**

        :param user: management user name, defaults to None
        :type user: str, optional
        :param password: password for the management user, defaults to None
        :type password: str, optional
        :param managementServers:  The string should be in the following format: \"<server name or IP>:<port>,<server name or IP>:<port>,...\", defaults to None
        :type managementServers: str, optional
        :param managementProtocol:  The management servers protocol, defaults to https
        :type managementProtocol: str, optional
        :raises ConnectionManagerError: If there was a problem connecting to the management server.
        """
        self.logger = Logger().getLogger('NVMeshSDK')

        if not managementServers:
            managementServers, managementProtocol = self.getManagementServersAndProtocolFromConfigs()

        managementServers = Utils.transformManagementClusterToUrls(managementServers, managementProtocol, httpServerPort='4000')

        if not dbUUID:
            dbUUID = self.getDBUUID(managementServers)

        try:
            if user is not None and password is not None:
                self.managementConnection = ConnectionManager.getInstance(dbUUID=dbUUID, user=user, password=password, logger=logger, managementServers=managementServers)
            else:
                self.managementConnection = ConnectionManager.getInstance(dbUUID=dbUUID, logger=logger, managementServers=managementServers)
        except ConnectionManagerError as e:
            raise e

    def getDBUUID(self, managementServers):
        err, result = ConfigurationVersionAPI(managementServersUrls=managementServers).getDBUUID()
        if err or not result:
            msg = 'Failed to resolve {} into DB UUID. '.format(managementServers)
            if err:
                msg += 'Error: {}'.format(err)

            self.logger.error(err)
            exit(1)

        return result['dbUUID']

    def initGetConfig(self):
        configs = Utils.readConfFile(BaseClassAPI.configFile)

        def getConfig(self, config):
            value = None

            if config in configs:
                value = configs[config]
            else:
                self.logger.error('{0} variable could not be found in : {1}'.format(config, BaseClassAPI.configFile))
                exit(1)

            return value
        return getConfig

    def getManagementServersAndProtocolFromConfigs(self):
        getConfig = self.initGetConfig()
        protocol = getConfig(self, 'MANAGEMENT_PROTOCOL')
        servers = getConfig(self, 'MANAGEMENT_SERVERS')
        return servers, protocol

    def changeManagementServers(self, managementServers):
        self.managementConnection.setManagementServers(managementServers)

    @classmethod
    def getEndpointRoute(cls):
        return ''

    def get(self, page=0, count=0, filter=None, sort=None, projection=None, route=None):
        routes = ['all'] if route is None else route
        query = Utils.buildQueryStr({'filter': filter, 'sort': sort, 'projection': projection})

        if page is None and count is None:
            routes[0] += query
        else:
            routes += ['{0}'.format(page), '{0}{1}'.format(count, query)]

        err, out = self.makeGet(routes)

        if out is not None:
            enteties = [self.getType()(**result) for result in out]
            for entity in enteties:
                entity.deserialize()
            return None, enteties
        else:
            return err, None

    def count(self):
        return self.makeGet(['count'])

    def save(self, entitiesList, postTimeout=None):
        return self.makePost(['save'], entitiesList, postTimeout)

    def update(self, entitiesList):
        return self.makePost(['update'], entitiesList)

    # calling delete from here indicates that delete eventually expects a list of id objects
    # if overridden in the child then delete expects a list of string ids
    # either way the sdk method will accept both
    def delete(self, entitiesList, postTimeout=None):
        if len(entitiesList) and not isinstance(entitiesList[0], self.getType()):
            entitiesList = self.getEntitesFromIds(entitiesList)

        return self.makePost(['delete'], entitiesList, postTimeout)

    def makePost(self, routes, objects, postTimeout=None):
        isObjects = [issubclass(obj.__class__, Entity) for obj in objects]
        if all(isObjects):
            payload = [obj.serialize() for obj in objects]
        else:
            payload = objects

        try:
            route = Utils.createRouteString(routes=routes, endPointRoute=self.getEndpointRoute())
            err, out = self.managementConnection.post(route, payload, postTimeout)

            return err, out
        except ConnectionManagerError as e:
            raise e

    def makeGet(self, routes):
        try:
            route = Utils.createRouteString(routes=routes, endPointRoute=self.getEndpointRoute())
            err, out = self.managementConnection.get(route)
            return err, out
        except ConnectionManagerError as e:
            raise e

    def getEntityIds(self, entities, idAttr='_id'):
        if isinstance(entities[0], self.getType()):
            entityIds = [getattr(entity, idAttr) for entity in entities]
        else:
            entityIds = entities

        return entityIds

    def getEntitesFromIds(self, ids, idAttr='_id'):
        return [{idAttr: id} for id in ids]

    def getType(self):
        pass
