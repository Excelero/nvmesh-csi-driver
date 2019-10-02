from NVMeshSDK.Entities.DriveClass import DriveClass
from NVMeshSDK.Entities.Drive import Drive
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class DriveClassAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.DISK_CLASSES

    def get(self, page=0, count=0, projection=None, filter=None, sort=None):
        """**Get drive classes by page and count, limit the result using filter, sort and projection**

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

            **out**: list of DriveClass entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveClassAPI import DriveClassAPI

                # fetching all the drive classes
                driveClassAPI = DriveClassAPI()
                err, out = driveClassAPI.get()

                >>> err
                None
                >>> for driveClass in out: print driveClass
                {
                    "_id": "dc1",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-08T08:00:08.527Z",
                    "dateModified": "2019-07-08T08:00:08.527Z",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800805.1"
                        },
                        {
                            "diskID": "S3HCNX0K800811.1"
                        },
                        {
                            "diskID": "S23YNAAH200345.1"
                        }
                    ],
                    "modifiedBy": "admin@excelero.com",
                    "tags": []
                }
                {
                    "_id": "dc2",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-08T08:06:01.575Z",
                    "dateModified": "2019-07-08T08:06:01.575Z",
                    "description": "2fast 2furious drives",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800805.1"
                        },
                        {
                            "diskID": "S3HCNX0K800808.1"
                        }
                    ],
                    "modifiedBy": "admin@excelero.com",
                    "tags": []
                }



                # fetching all drive classes and projecting only the id and drives of each drive class using MongoObj and DriveClass class attributes
                from NVMeshSDK.Entities.DriveClass import DriveClass
                from NVMeshSDK.MongoObj import MongoObj
                err, out = driveClassAPI.get(projection=[MongoObj(field=DriveClass.Drives, value=1), MongoObj(field=DriveClass.Id, value=1)])

                >>> err
                None
                >>> for driveClass in out: print driveClass
                {
                    "_id": "dc1",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800805.1"
                        },
                        {
                            "diskID": "S3HCNX0K800811.1"
                        },
                        {
                            "diskID": "S23YNAAH200345.1"
                        }
                    ]
                }
                {
                    "_id": "dc2",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800805.1"
                        },
                        {
                            "diskID": "S3HCNX0K800808.1"
                        }
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
        return super(DriveClassAPI, self).get(page=page, count=count, projection=projection, filter=filter, sort=sort)

    def save(self, driveClasses):
        """**Save drive classes**

        :param driveClasses: list of DriveClass entities
        :type driveClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveClassAPI import DriveClassAPI

                # creating 2 drive classes using their DriveClass entity and Drive entity
                from NVMeshSDK.Entities.DriveClass import DriveClass
                dc1 = DriveClass(_id="dc1", disks=[Drive(diskID="S3HCNX0K800427.1")])
                dc2 = DriveClass(_id="dc2", disks=[Drive(diskID="S3HCNX0K800427.1"), Drive(diskID="S3HCNX0K701203.1")])

                driveClassAPI = DriveClassAPI()
                err, out = driveClassAPI.save([dc1, dc2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'dc1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'dc2',
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
                        u'_id': u'dc1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'dc2',
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
        for driveClass in driveClasses:
            if not isinstance(driveClass.disks[0], Drive):
                drives = self.getEntitesFromIds(ids=driveClass.disks, idAttr=Drive.Id.dbKey)
                setattr(driveClass, DriveClass.Drives.dbKey, drives)

        return self.makePost(['save'], driveClasses)

    def update(self, driveClasses):
        """**Update drive classes**

        :param driveClasses: list of DriveClass entities
        :type driveClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveClassAPI import DriveClassAPI

                # updating a drive class
                from NVMeshSDK.Entities.DriveClass import DriveClass
                from NVMeshSDK.MongoObj import MongoObj

                err, dcs = driveClassAPI.get(filter=[MongoObj(field=DriveClass.Id, value="dc1")])
                dc1 = dcs[0]
                >>> print dc1
                {
                    "_id": "dc1",
                    "createdBy": "app@excelero.com",
                    "dateCreated": "2019-07-08T14:32:29.808Z",
                    "dateModified": "2019-07-08T14:32:29.808Z",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800427.1"
                        }
                    ],
                    "modifiedBy": "app@excelero.com"
                }

                dc1.disks.append(Drive(diskID="S3HCNX0K701203.1"))
                >>> print dc1
                {
                    "_id": "dc1",
                    "createdBy": "app@excelero.com",
                    "dateCreated": "2019-07-08T14:32:29.808Z",
                    "dateModified": "2019-07-08T14:32:29.808Z",
                    "disks": [
                        {
                            "diskID": "S3HCNX0K800427.1"
                        },
                        {
                            "diskID": "S3HCNX0K701203.1"
                        }
                    ],
                    "modifiedBy": "app@excelero.com"
                }


                driveClassAPI = DriveClassAPI()
                err, out = driveClassAPI.update([dc1])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'dc1',
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
                        u'_id': u'dc1',
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
        return super(DriveClassAPI, self).update(entitiesList=driveClasses)

    def delete(self, driveClasses):
        """**Delete drive classes**

        :param driveClasses: list of drive classes ids or DriveClass entities
        :type driveClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveClassAPI import DriveClassAPI

                # deleting 2 drive classes using their ids
                driveClassAPI = DriveClassAPI()
                err, out = driveClassAPI.delete(['dc1','dc2'])

                # deleting all drive classes, first using the 'get' method to get all the drive classes
                # as drive class entities list then passing it to the 'delete' method
                err, currentDCs = driveClassAPI.get()
                err, out = driveClassAPI.delete(currentDCs)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'dc1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'dc2',
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
                        u'_id': u'dc1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'dc2',
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
        return super(DriveClassAPI, self).delete(entitiesList=driveClasses)

    def count(self):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return DriveClass
