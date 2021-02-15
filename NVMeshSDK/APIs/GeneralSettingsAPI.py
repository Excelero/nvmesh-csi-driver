from NVMeshSDK.Entities.GeneralSettings import GeneralSettings
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes
from NVMeshSDK.MongoObj import MongoObj
from NVMeshSDK.Utils import Utils


class GeneralSettingsAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.GENERAL_SETTINGS

    def getClusterName(self):
        return self.get(projection=[MongoObj(field=GeneralSettings.ClusterName, value=1)])

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return GeneralSettings

    def get(self, projection=None):
        return super(GeneralSettingsAPI, self).get(page=None, count=None, projection=projection)

    def save(self, entitiesList, postTimeout=None):
        raise NotImplemented

    def count(self):
        raise NotImplemented

    def delete(self, entitiesList, postTimeout=None):
        raise NotImplemented