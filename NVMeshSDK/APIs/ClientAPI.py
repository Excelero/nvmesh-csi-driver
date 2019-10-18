"""
.. module:: ClientAPI
   :synopsis: All the functions of the Client API are defined here
.. moduleauthor:: Excelero
"""

from NVMeshSDK.Entities.Client import Client
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class ClientAPI(BaseClassAPI):
    """**All the functions of the Client API are defined here**"""
    endpointRoute = EndpointRoutes.CLIENTS

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        """**Get clients by page and count, limit the result using filter, sort and projection**

        :param page: The page to fetch, defaults to 0
        :type page: int, optional
        :param count: Number of records per page, defaults to 0
        :type count: int, optional
        :param filter: Filter before fetching using MongoDB filter objects, defaults to None
        :type filter: list, optional
        :param sort: Sort before fetching using MongoDB filter objects, defaults to None
        :type sort: list, optional
        :param projection: Project before fetching using MongoDB filter objects, defaults to None
        :type projection: list, optional
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: list of Client entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ClientAPI import ClientAPI

                # fetching all the clients
                clientAPI = ClientAPI()
                err, out = clientAPI.get()

                >>> err
                None
                >>> for client in out: print client
                {
                    "_id": "client-1@excelero.com",
                    "block_devices": [
                        {
                            "io_perm": 3,
                            "is_hidden": 1,
                            "name": "smvol2",
                            "uuid": "af570430-a089-11e9-a1f2-39ff57f28f65",
                            "vol_status": 2
                        }
                    ],
                    "branch": "1.3",
                    "client_id": "client-1@excelero.com",
                    "client_status": 1,
                    "commit": "7386c85",
                    "configuration_version": -1,
                    "connectionSequence": 3,
                    "controlJobs": [],
                    "dateModified": "2019-07-07T10:50:23.869Z",
                    "health": "healthy",
                    "health_old": "healthy",
                    "messageSequence": 313,
                    "version": "1.3.1-659"
                }
                {
                    "_id": "client-2@excelero.com",
                    "block_devices": [
                        {
                            "io_perm": 13,
                            "is_hidden": 0,
                            "is_io_enabled": 1,
                            "name": "jbod2",
                            "uuid": "b06bcf90-a089-11e9-a1f2-39ff57f28f65",
                            "vol_status": 4
                        }
                    ],
                    "branch": "1.3",
                    "client_id": "client-2@excelero.com",
                    "client_status": 1,
                    "commit": "7386c85",
                    "configuration_version": -1,
                    "connectionSequence": 3,
                    "controlJobs": [],
                    "dateModified": "2019-07-07T10:50:23.030Z",
                    "health": "healthy",
                    "health_old": "healthy",
                    "messageSequence": 295,
                    "version": "1.3.1-659"
                }


                # fetching all clients and projecting only the id of each client using MongoObj and Client's class attribute
                from NVMeshSDK.Entities.Client import Client
                from NVMeshSDK.MongoObj import MongoObj
                err, out = clientAPI.get(projection=[MongoObj(field=Client.Id, value=1)])

                >>> err
                None
                >>> for client in out: print client
                {
                    "_id": "client-1@excelero.com"
                }
                {
                    "_id": "client-2@excelero.com"
                }

            - Expected HTTP Fail Response::

                >>> err
                {
                    'code': <Return Code>,
                    'content': <Failure Details>,
                    'message': <Failure Reason>
                }

                >>> out
                None
        """
        return super(ClientAPI, self).get(page=page, count=count, filter=filter, sort=sort, projection=projection)

    # entity or id
    def delete(self, clients):
        """**Delete clients**

        :param clients: list of client ids or Client entities
        :type clients: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ClientAPI import ClientAPI

                # deleting 2 clients using their ids
                clientAPI = ClientAPI()
                err, out = clientAPI.delete(clients=['client-1@excelero.com','client-2@excelero.com'])

                # deleting all clients, first using the 'get' method to get all the clients
                # as client entities list then passing it to the 'delete' method
                err, currentClients = clientAPI.get()
                err, out = clientAPI.delete(currentClients)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'client-1@excelero.com',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'client-2@excelero.com',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    }
                ]

            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'client-1@excelero.com',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'client-2@excelero.com',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    }
                ]

            - Expected HTTP Fail Response::

                >>> err
                {
                    'code': <Return Code>,
                    'content': <Failure Details>,
                    'message': <Failure Reason>
                }

                >>> out
                None
        """
        return self.makePost(routes=['delete'], objects={'Ids': self.getEntityIds(clients)})

    def count(self):
        """**Get total clients count.**

        :return: clients count
        :rtype: int

         - Example::

                from NVMeshSDK.APIs.ClientAPI import ClientAPI

                clientAPI = ClientAPI()
                err, out = clientAPI.count()

                >>> err
                None
                >>> out
                2

            - Expected HTTP Fail Response::

                >>> err
                {
                    'code': <Return Code>,
                    'content': <Failure Details>,
                    'message': <Failure Reason>
                }

                >>> out
                None
        """
        return super(ClientAPI, self).count()

    def save(self, entitiesList):
        raise NotImplemented

    def update(self, entitiesList):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return Client


