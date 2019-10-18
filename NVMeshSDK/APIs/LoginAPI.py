from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class LoginAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.LOGIN

    def login(self, user, password):
        return self.makePost([''], {'username': user, 'password': password})

    def logout(self):
        return self.makeGet(['logout'])

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute
