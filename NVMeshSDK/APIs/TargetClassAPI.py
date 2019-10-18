from NVMeshSDK.Entities.TargetClass import TargetClass
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class TargetClassAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.SERVER_CLASSES

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        """**Get target classes by page and count, limit the result using filter, sort and projection**

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

            **out**: list of TargetClass entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI

                # fetching all the target classes
                targetClassAPI = TargetClassAPI()
                err, out = targetClassAPI.get()

                >>> err
                None
                >>> for targetClass in out: print targetClass
               {
                    "_id": "tc1",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-07T14:56:17.500Z",
                    "dateModified": "2019-07-07T14:56:17.500Z",
                    "modifiedBy": "admin@excelero.com",
                    "name": "tc1",
                    "servers": [],
                    "targetNodes": [
                        "nvme71",
                        "nvme77"
                    ]
                }
                {
                    "_id": "tc2",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-07T14:56:23.742Z",
                    "dateModified": "2019-07-07T14:56:23.742Z",
                    "modifiedBy": "admin@excelero.com",
                    "name": "tc2",
                    "servers": [],
                    "targetNodes": [
                        "nvme89"
                    ]
                }


                # fetching all target classes and projecting only the id and target nodes of each target class using MongoObj and TargetClass class attributes
                from NVMeshSDK.Entities.TargetClass import TargetClass
                from NVMeshSDK.MongoObj import MongoObj
                err, out = targetClassAPI.get(projection=[MongoObj(field=TargetClass.TargetNodes, value=1), MongoObj(field=TargetClass.Id, value=1)])

                >>> err
                None
                >>> for targetClass in out: print targetClass
                {
                    "_id": "tc1",
                    "name": "tc1",
                    "targetNodes": [
                        "nvme71",
                        "nvme77"
                    ]
                }
                {
                    "_id": "tc2",
                    "name": "tc2",
                    "targetNodes": [
                        "nvme89"
                    ]
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
        return super(TargetClassAPI, self).get(count=count, page=page, filter=filter, sort=sort, projection=projection)

    def save(self, targetClasses):
        """**Save target classes**

        :param targetClasses: list of TargetClass entities
        :type targetClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI

                # creating 2 target classes using their TargetClass entity
                from NVMeshSDK.Entities.TargetClass import TargetClass
                tc1 = TargetClass(name="tc1", targetNodes=["target1.excelero.com", "target2.excelero.com"])
                tc2 = TargetClass(name="tc2", targetNodes=["target3.excelero.com"], description="Super computer")

                targetClassAPI = TargetClassAPI()
                err, out = targetClassAPI.save([tc1, tc2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'tc1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'tc2',
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
                        u'_id': u'tc1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'tc2',
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
        return super(TargetClassAPI, self).save(entitiesList=targetClasses)

    def update(self, targetClasses):
        """**Update target classes**

        :param targetClasses: list of TargetClass entities
        :type targetClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI

                # updating a target class
                from NVMeshSDK.Entities.TargetClass import TargetClass
                from NVMeshSDK.MongoObj import MongoObj
                err, tcs = targetClassAPI.get(filter=[MongoObj(field=TargetClass.Id, value="tc1")])
                tc1 = tcs[0]
                >>> print tc1
                {
                    "_id": "tc1",
                    "name": "tc1",
                    "targetNodes": [
                        "target1.excelero.com",
                        "target2.excelero.com"
                    ]
                }
                tc1.targetNodes.append("target66.excelero.com")
                >>> print tc1
                {
                    "_id": "tc1",
                    "name": "tc1",
                    "targetNodes": [
                        "target1.excelero.com",
                        "target2.excelero.com",
                        "target66.excelero.com"
                    ]
                }

                targetClassAPI = TargetClassAPI()
                err, out = targetClassAPI.update([tc1])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'tc1',
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
                        u'_id': u'tc1',
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
        return super(TargetClassAPI, self).update(entitiesList=targetClasses)

    def delete(self, targetClasses):
        """**Delete target classes**

        :param targetClasses: list of target classes ids or TargetClass entities
        :type targetClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI

                # deleting 2 target classes using their ids
                targetClassAPI = TargetClassAPI()
                err, out = targetClassAPI.delete(['tc1','tc2'])

                # deleting all target classes, first using the 'get' method to get all the target classes
                # as target class entities list then passing it to the 'delete' method
                err, currentTCs = targetClassAPI.get()
                err, out = targetClassAPI.delete(currentTCs)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'tc1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'tc2',
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
                        u'_id': u'tc1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'tc2',
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
        return super(TargetClassAPI, self).delete(entitiesList=targetClasses)

    def count(self):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return TargetClass
