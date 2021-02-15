from NVMeshSDK.Entities.MongoDB import MongoDB
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class MongoDBAPI(BaseClassAPI):

    endpointRoute = EndpointRoutes.MONGO_DB

    def get(self):
        """**Get MongoDB status.**

        :return: MongoDB entity
        :rtype: MongoDB

        - Example::

            from NVMeshSDK.APIs.MongoDBAPI import MongoDBAPI

            mongoDBAPI = MongoDBAPI()
            err, out = mongoDBAPI.get()

            >>> err
            None
            >>> print out
            {
                "members": [
                    {
                        "_id": 0,
                        "configVersion": 3,
                        "dbSize": 89948,
                        "electionDate": "2020-08-16T14:33:54.000Z",
                        "electionTime": "6861590076497854465",
                        "freeSpace": 42499002368,
                        "health": 1,
                        "host": "nvme51.excelero.com",
                        "infoMessage": "",
                        "lastHeartbeatMessage": "",
                        "name": "nvme51.excelero.com:27017",
                        "optime": {
                            "t": 6,
                            "ts": "6861593512471691267"
                        },
                        "optimeDate": "2020-08-16T14:47:14.000Z",
                        "port": "27017",
                        "state": 1,
                        "stateStr": "PRIMARY",
                        "syncSourceHost": "",
                        "syncSourceId": -1,
                        "syncingTo": "",
                        "uptime": 813
                    },
                    {
                        "_id": 1,
                        "configVersion": 3,
                        "dbSize": 335230,
                        "freeSpace": 43456790528,
                        "health": 1,
                        "host": "10.0.1.53",
                        "infoMessage": "",
                        "lastHeartbeat": "2020-08-16T14:47:14.668Z",
                        "lastHeartbeatMessage": "",
                        "lastHeartbeatRecv": "2020-08-16T14:47:13.640Z",
                        "name": "10.0.1.53:27017",
                        "optime": {
                            "t": 6,
                            "ts": "6861593508176723971"
                        },
                        "optimeDate": "2020-08-16T14:47:13.000Z",
                        "optimeDurable": {
                            "t": 6,
                            "ts": "6861593508176723971"
                        },
                        "optimeDurableDate": "2020-08-16T14:47:13.000Z",
                        "pingMs": 0,
                        "port": "27017",
                        "state": 2,
                        "stateStr": "SECONDARY",
                        "syncSourceHost": "10.0.1.65:27017",
                        "syncSourceId": 2,
                        "syncingTo": "10.0.1.65:27017",
                        "uptime": 811
                    },
                    {
                        "_id": 2,
                        "configVersion": 3,
                        "dbSize": 335224,
                        "freeSpace": 43819982848,
                        "health": 1,
                        "host": "10.0.1.65",
                        "infoMessage": "",
                        "lastHeartbeat": "2020-08-16T14:47:14.669Z",
                        "lastHeartbeatMessage": "",
                        "lastHeartbeatRecv": "2020-08-16T14:47:13.622Z",
                        "name": "10.0.1.65:27017",
                        "optime": {
                            "t": 6,
                            "ts": "6861593508176723971"
                        },
                        "optimeDate": "2020-08-16T14:47:13.000Z",
                        "optimeDurable": {
                            "t": 6,
                            "ts": "6861593508176723971"
                        },
                        "optimeDurableDate": "2020-08-16T14:47:13.000Z",
                        "pingMs": 0,
                        "port": "27017",
                        "state": 2,
                        "stateStr": "SECONDARY",
                        "syncSourceHost": "nvme51.excelero.com:27017",
                        "syncSourceId": 0,
                        "syncingTo": "nvme51.excelero.com:27017",
                        "uptime": 811
                    }
                ],
                "set": "rs0"
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
        return super(MongoDBAPI, self).get(page=None, count=None, filter=None, sort=None, projection=None)

    def delete(self, entitiesList):
        raise NotImplemented

    def save(self, entitiesList):
        raise NotImplemented

    def update(self, entitiesList):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return MongoDB