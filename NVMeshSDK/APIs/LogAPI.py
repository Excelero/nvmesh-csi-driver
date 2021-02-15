from NVMeshSDK.Entities.Log import Log
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class LogAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.LOGS
    
    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        """**Get logs by page and count, limit the result using filter and sort**

        :param filter: Filter before fetching using MongoDB filter objects, defaults to None
        :type filter: list, optional
        :param sort: Sort before fetching using MongoDB filter objects, defaults to None
        :type sort: list, optional
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: list of VPG entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.LogAPI import LogAPI

                # fetching only logs that their message contains 'new Client', using MongoObj, mongo $regex operator and Log class attributes
                from NVMeshSDK.Entities.Log import Log
                from NVMeshSDK.MongoObj import MongoObj

                logAPI = LogAPI()

                err ,out = logAPI.get(filter=[MongoObj(field=Log.Message, value={"$regex": "new Client", "$options": 'i'})])

                >>> err
                None
                >>> for log in out: print log
                {
                    "_id": "5d2611381e1c9d3f0730afa3",
                    "level": "INFO",
                    "message": "New client: scale-2.excelero.com",
                    "meta": {
                        "acknowledged": false,
                        "header": "New client",
                        "link": {
                            "entityText": "scale-2.excelero.com",
                            "entityType": "CLIENT"
                        },
                        "rawMessage": "New client: {}"
                    },
                    "timestamp": "2019-07-10T16:24:24.856Z"
                }
                {
                    "_id": "5d2611381e1c9d3f0730afa4",
                    "level": "INFO",
                    "message": "New client: scale-1.excelero.com",
                    "meta": {
                        "acknowledged": false,
                        "header": "New client",
                        "link": {
                            "entityText": "scale-1.excelero.com",
                            "entityType": "CLIENT"
                        },
                        "rawMessage": "New client: {}"
                    },
                    "timestamp": "2019-07-10T16:24:24.872Z"
                }
                {
                    "_id": "5d26113a1e1c9d3f0730afe3",
                    "level": "INFO",
                    "message": "New client: scale-3.excelero.com",
                    "meta": {
                        "acknowledged": false,
                        "header": "New client",
                        "link": {
                            "entityText": "scale-3.excelero.com",
                            "entityType": "CLIENT"
                        },
                        "rawMessage": "New client: {}"
                    },
                    "timestamp": "2019-07-10T16:24:26.490Z"
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
        return super(LogAPI, self).get(page=page, count=count, filter=filter, sort=sort, projection=projection)

    def getAlerts(self, page=0, count=0, filter=None, sort=None):
        """**Get alerts (errors that hasn't been acknowledged) by page and count, limit the result using filter and sort**

        :param filter: Filter before fetching using MongoDB filter objects, defaults to None
        :type filter: list, optional
        :param sort: Sort before fetching using MongoDB filter objects, defaults to None
        :type sort: list, optional
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: list of VPG entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.LogAPI import LogAPI

                # fetching only alerts that their message contains 'drive', using MongoObj, mongo $regex operator and Log class attributes
                from NVMeshSDK.Entities.Log import Log
                from NVMeshSDK.MongoObj import MongoObj

                logAPI = LogAPI()

                err ,out = logAPI.get(filter=[MongoObj(field=Log.Message, value={"$regex": "drive", "$options": 'i'})])

                >>> err
                None
                >>> for alert in out: print alert
                {
                    "_id": "5d2c52d479a4fe562155ac07",
                    "level": "WARNING",
                    "message": "The drive: SGFPZKBRMQ6Q.9 was automatically evicted for the following reason: 'Drive was imported from another NVMesh environment'",
                    "meta": {
                        "acknowledged": false,
                        "header": "Drive automatically evicted",
                        "link": {
                            "entityText": "SGFPZKBRMQ6Q.9",
                            "entityType": "DISK",
                            "target": "scale-1.excelero.com"
                        },
                        "rawMessage": "The drive: {} was automatically evicted for the following reason: 'Drive was imported from another NVMesh environment'"
                    },
                    "timestamp": "2019-07-15T10:17:56.506Z"
                }
                {
                    "_id": "5d2c52d479a4fe562155ac08",
                    "level": "ERROR",
                    "message": "Drive: SGFPZKBRMQ6Q.9 reported status: Ok and health: critical",
                    "meta": {
                        "acknowledged": false,
                        "header": "Drive failure",
                        "link": {
                            "entityText": "SGFPZKBRMQ6Q.9",
                            "entityType": "DISK",
                            "target": "scale-1.excelero.com"
                        },
                        "rawMessage": "Drive: {} reported status: Ok and health: critical"
                    },
                    "timestamp": "2019-07-15T10:17:56.506Z"
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
        return super(LogAPI, self).get(page=page, count=count, filter=filter, sort=sort, route=['alerts'])

    def acknowledgeAll(self):
        """***Acknowledge all logged alerts.***

        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per log or None if there was an HTTP error
        :rtype: tuple

        - Example::

                from NVMeshSDK.APIs.LogAPI import LogAPI

                logAPI = LogAPI()
                err, out = logAPI.acknowledgeAll()

            - Expected Success Response::

                >>> err
                None

                >>> out
                 {
                    u'_id': None,
                    u'error': None,
                    u'payload': None,
                    u'success': True
                }


            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                {
                    u'_id': None,
                    u'error': <Failure Reason>,
                    u'payload': None,
                    u'success': False
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
        return self.makePost(routes=['acknowledgeAll'], objects={})

    # entity or id
    def acknowledgeLogs(self, logs):
        """***Acknowledge specified logs.***

        :param logs: list of logs ids or Log entities
        :type logs: list
        :return: list of tuples (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per log or None if there was an HTTP error
        :rtype: list

        - Example::

                from NVMeshSDK.APIs.LogAPI import LogAPI

                # acknowledge 3 logs using their ids
                logAPI = LogAPI()
                out = logAPI.acknowledgeLogs(logs=['5d2611381e1c9d3f0730afa3', '5d2611381e1c9d3f0730afa4', '5d26113a1e1c9d3f0730afe3'])

                # Acknowledge only logs that their message contains 'new Client'.
                # First using using the 'get' method with MongoObj, mongo $regex operator and Log class attributes to fetch the logs
                # as Log entities list then passing it to the 'acknowledgeLogs' method.
                err ,newClientLogs = logAPI.get(filter=[MongoObj(field=Log.Message, value={"$regex": "new Client", "$options": 'i'})])
                out = logAPI.acknowledgeLogs(newClientLogs)

            - Expected Success Response::

                >>> out
                [
                    (None, {
                            u'_id': u'5d2611381e1c9d3f0730afa3',
                            u'error': None,
                            u'payload': None,
                            u'success': True
                            }
                    ),
                    (None, {
                            u'_id': u'5d2611381e1c9d3f0730afa4',
                            u'error': None,
                            u'payload': None,
                            u'success': True
                            }
                    ),
                    (None, {
                            u'_id': u'5d26113a1e1c9d3f0730afe3',
                            u'error': None,
                            u'payload': None,
                            u'success': True
                            }
                    )
                ]


            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                [
                    (None, {
                            u'_id': u'5d2611381e1c9d3f0730afa3',
                            u'error': <Failure Reason>,
                            u'payload': None,
                            u'success': False
                            }
                    ),
                    (None, {
                            u'_id': u'5d2611381e1c9d3f0730afa4',
                            u'error': <Failure Reason>,
                            u'payload': None,
                            u'success': False
                            }
                    ),
                    (None, {
                            u'_id': u'5d26113a1e1c9d3f0730afe3',
                            u'error': None,
                            u'payload': None,
                            u'success': True
                            }
                    )
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
        return [self.makePost(routes=['acknowledge'], objects={'id': logId}) for logId in self.getEntityIds(logs)]

    def countAlerts(self):
        """**Get total alerts count.**

               :return: alerts count
               :rtype: int

                - Example::

                       from NVMeshSDK.APIs.LogAPI import LogAPI

                       logAPI = LogAPI()
                       err, out = LogAPI.countAlerts()

                       >>> err
                       None
                       >>> out
                       122

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
        return self.makeGet(routes=['alerts', 'count'])

    def count(self):
        """**Get total logs count.**

               :return: logs count
               :rtype: int

                - Example::

                       from NVMeshSDK.APIs.LogAPI import LogAPI

                       logAPI = LogAPI()
                       err, out = LogAPI.count()

                       >>> err
                       None
                       >>> out
                       3606

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
        return super(LogAPI, self).count()

    def save(self, entitiesList):
        raise NotImplemented

    def update(self, entitiesList):
        raise NotImplemented

    def delete(self, entitiesList):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return Log


class AlertAPI(LogAPI):
    def count(self):
        return super(AlertAPI, self).countAlerts()

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        return super(AlertAPI, self).getAlerts(page=page, count=count, filter=filter, sort=sort)