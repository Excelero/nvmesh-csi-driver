from NVMeshSDK.Entities.Volume import Volume
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class VolumeAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.VOLUMES

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        """**Get volumes by page and count, limit the result using filter, sort and projection**

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

            **out**: list of Volume entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeAPI import VolumeAPI

                # fetching all the volumes and projecting only some attributes using MongoObj and Volume class attributes
                from NVMeshSDK.Entities.Volume import Volume
                from NVMeshSDK.MongoObj import MongoObj

                volumeAPI = VolumeAPI()

                myProj = [MongoObj(field=Volume.Id, value=1), MongoObj(field=Volume.Size, value=1), MongoObj(field=Volume.RaidLevel, value=1)]
                err, out = volumeAPI.get(projection=myProj)

                >>> err
                None
                >>> for volume in out: print volume
                {
                    "RAIDLevel": "Mirrored RAID-1",
                    "_id": "vm132-82v2",
                    "capacity": 5000000000,
                    "name": "vm132-82v2"
                }
                {
                    "RAIDLevel": "Mirrored RAID-1",
                    "_id": "vm132-89v1",
                    "capacity": 5000000000,
                    "name": "vm132-89v1"
                }
                {
                    "RAIDLevel": "Mirrored RAID-1",
                    "_id": "vm132-94v2",
                    "capacity": 5000000000,
                    "name": "vm132-94v2"
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
        return super(VolumeAPI, self).get(page=page, count=count, filter=filter, sort=sort, projection=projection)

    def delete(self, volumes):
        """**Delete volumes**

        :param volumes: list of volumes ids or Volume entities
        :type volumes: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeAPI import VolumeAPI

                # deleting 2 volumes using their ids
                volumeAPI = VolumeAPI()
                err, out = volumeAPI.delete(['jvol', 'mvol'])

                # deleting all volumes, first using the 'get' method to get all the volumes
                # as Volume entities list then passing it to the 'delete' method
                err, currentVolumes = volumeAPI.get()
                err, out = volumeAPI.delete(currentVolumes)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'jvol',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'mvol',
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
                        u'_id': u'jvol',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'mvol',
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
        return super(VolumeAPI, self).delete(entitiesList=volumes)

    def save(self, volumes):
        """**Save volumes**

        :param volumes: list of Volume entities
        :type volumes: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeAPI import VolumeAPI

                # creating 2 volumes using the Volume entity
                from NVMeshSDK.Entities.Volume import Volume

                vol1 = Volume(name="vol1", RAIDLevel="Mirrored RAID-1", capacity=1024**3, numberOfMirrors=1)
                vol2 = Volume(name="vol2", RAIDLevel="Concatenated", capacity=1024**3, description="some description")

                volumeAPI = VolumeAPI()
                err, out = volumeAPI.save([vol1, vol2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vol1',
                        u'error': None,
                        u'payload': {u'isReserved': False},
                        u'success': True
                    },
                    {
                        u'_id': u'vol2',
                        u'error': None,
                        u'payload': {u'isReserved': False},
                        u'success': True
                    }
                ]

            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vol1',
                        u'error': <Failure Reason>,
                        u'payload': {u'isReserved': False},
                        u'success': False
                    },
                    {
                        u'_id': u'vol2',
                        u'error': <Failure Reason>,
                        u'payload': {u'isReserved': False},
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
        return super(VolumeAPI, self).save(entitiesList=volumes)

    def update(self, volumes):
        """**Update volumes**

        :param volumes: list of Volume entities
        :type volumes: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeAPI import VolumeAPI

                # updating a volume - doubling its capacity
                from NVMeshSDK.Entities.Volume import Volume
                from NVMeshSDK.MongoObj import MongoObj

                err, volumes = volumeAPI.get(filter=[MongoObj(field=Volume.Id, value="vol2")])
                myVol = volumes[0]

                >>> print myVol
                {
                    "RAIDLevel": "Concatenated",
                    "_id": "vol2",
                    "blockSize": 4096,
                    "blocks": 2441376,
                    "capacity": 10000000000,
                    "chunks": [
                        {
                            "_id": "b0533eb0-a31f-11e9-bac1-d7b83d0e8ab3",
                            "pRaids": [
                                {
                                    "activated": false,
                                    "diskSegments": [
                                        {
                                            "_id": "b0533eb1-a31f-11e9-bac1-d7b83d0e8ab3",
                                            "allocationIndex": 0,
                                            "diskID": "SGFPZKBRMQ6Q.5",
                                            "diskUUID": "6d1014b0-a24e-11e9-bac1-d7b83d0e8ab3",
                                            "lbe": 48627135,
                                            "lbs": 46185760,
                                            "nodeUUID": "6d0d0770-a24e-11e9-bac1-d7b83d0e8ab3",
                                            "node_id": "scale-1.excelero.com",
                                            "pRaidIndex": 0,
                                            "pRaidTypeIndex": 0,
                                            "pRaidUUID": "b05365c0-a31f-11e9-bac1-d7b83d0e8ab3",
                                            "status": "normal",
                                            "type": "data",
                                            "uuid": "b0533eb1-a31f-11e9-bac1-d7b83d0e8ab3",
                                            "volumeName": "vol2",
                                            "volumeUUID": "b04fbc40-a31f-11e9-bac1-d7b83d0e8ab3"
                                        }
                                    ],
                                    "stripeIndex": 0,
                                    "tomaLeaderConnectionSequence": 1,
                                    "tomaLeaderRaftTerm": -1,
                                    "uuid": "b05365c0-a31f-11e9-bac1-d7b83d0e8ab3",
                                    "version": {
                                        "major": 1,
                                        "minor": 0
                                    }
                                }
                            ],
                            "uuid": "b0533eb0-a31f-11e9-bac1-d7b83d0e8ab3",
                            "vlbe": 2441375,
                            "vlbs": 0
                        }
                    ],
                    "createdBy": "app@excelero.com",
                    "dateCreated": "2019-07-10T14:33:30.887Z",
                    "dateModified": "2019-07-10T14:33:30.756Z",
                    "description": "some description",
                    "health": "critical",
                    "isReserved": false,
                    "lockServer": {
                        "locksetShift": -1,
                        "maxNOwners": 1,
                        "type": 2
                    },
                    "modifiedBy": "app@excelero.com",
                    "name": "vol2",
                    "numberOfMirrors": 0,
                    "relativeRebuildPriority": 10,
                    "status": "unavailable",
                    "type": "normal",
                    "uuid": "b04fbc40-a31f-11e9-bac1-d7b83d0e8ab3",
                    "version": 1
                }

                myVol.capacity *= 2

                >>> print myVol
                {
                    "RAIDLevel": "Concatenated",
                    "_id": "vol2",
                    "blockSize": 4096,
                    "blocks": 2441376,
                    "capacity": 20000000000,
                    "chunks": [...],
                    "createdBy": "app@excelero.com",
                    "dateCreated": "2019-07-10T14:33:30.887Z",
                    "dateModified": "2019-07-10T14:33:30.756Z",
                    "description": "some description",
                    "health": "critical",
                    "isReserved": false,
                    "lockServer": {
                        "locksetShift": -1,
                        "maxNOwners": 1,
                        "type": 2
                    },
                    "modifiedBy": "app@excelero.com",
                    "name": "vol2",
                    "numberOfMirrors": 0,
                    "relativeRebuildPriority": 10,
                    "status": "unavailable",
                    "type": "normal",
                    "uuid": "b04fbc40-a31f-11e9-bac1-d7b83d0e8ab3",
                    "version": 1
                }


                volumeAPI = VolumeAPI()
                err, out = volumeAPI.update([myVol])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vol2',
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
                        u'_id': u'vol2  ',
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
        return super(VolumeAPI, self).update(entitiesList=volumes)

    # entity or id
    def rebuildVolumes(self, volumes):
        """**Rebuild Volumes**

        :param volumes: list of volume ids or Volume entities
        :type volumes: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeAPI import VolumeAPI

                # rebuild 2 volumes using their ids
                volumeAPI = VolumeAPI()
                err, out = volumeAPI.rebuildVolumes(["jvol", "mvol"])

                # rebuild 2 volumes using their Volume entity
                # fetching the volumes via get method using MonogObj and mongo $in operator, then passing it to the rebuildVolumes method
                from NVMeshSDK.Entities.Volume import Volume
                from NVMeshSDK.MongoObj import MongoObj

                err, myVolumes = volumeAPI.get(filter=[MongoObj(field=Volume.Id, value={"$in": ['vm131-4v2', 'vm131-9v1']})])
                err, out = volumeAPI.rebuildVolumes(myVolumes)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'jvol',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'mvol',
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
                        u'_id': u'jvol',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'mvol',
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
        return self.makePost(routes=['rebuildVolumes'], objects=self.getEntityIds(volumes))

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return Volume
