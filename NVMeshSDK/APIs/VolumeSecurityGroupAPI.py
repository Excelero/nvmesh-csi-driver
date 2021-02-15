from NVMeshSDK.Entities.VolumeSecurityGroup import VolumeSecurityGroup
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class VolumeSecurityGroupAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.VolumeSecurityGroups

    def get(self, page=0, count=0, projection=None, filter=None, sort=None):
        """**Get VSGs by page and count, limit the result using filter, sort and projection**

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

            **out**: list of VolumeSecurityGroup entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeSecurityGroupAPI import VolumeSecurityGroupAPI

                # fetching all the VSGs
                volumeSecurityGroupAPI = VolumeSecurityGroupAPI()
                err, out = volumeSecurityGroupAPI.get()

                >>> err
                None
                >>> for vsg in out: print vsg
                {
                    "_id": "vsg1",
                    "description": "some description",
                    "keys": ["key1", "key2"],
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z")
                }
                {
                    "_id": "vsg2",
                    "description": "some description!!!",
                    "keys": ["key2", "key4"],
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:55.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:55.136Z")
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
        return super(VolumeSecurityGroupAPI, self).get(page=page, count=count, projection=projection, filter=filter, sort=sort)

    def save(self, vsgs):
        """**Save VSGs**

        :param vsgs: list of VolumeSecurityGroup entities
        :type vsgs: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeSecurityGroupAPI import VolumeSecurityGroupAPI

                # creating 2 VSGs using the VolumeSecurityGroup entity
                from NVMeshSDK.Entities.VolumeSecurityGroupAPI import VolumeSecurityGroupAPI
                vsg1 = VolumeSecurityGroup(_id="vsg1", description="VSG 1", keys=["key1", "key2"])
                vsg2 = VolumeSecurityGroup(_id="vsg2", description="VSG 2")

                volumeSecurityGroupAPI = VolumeSecurityGroupAPI()
                err, out = volumeSecurityGroupAPI.save([vsg1, vsg2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vsg1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'vsg2',
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
                        u'_id': u'vsg1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'vsg2',
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
        return super(VolumeSecurityGroupAPI, self).save(entitiesList=vsgs)

    def update(self, vsgs):
        """**Update VSGs**

        :param vsgs: list of VolumeSecurityGroup entities
        :type vsgs: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeSecurityGroupAPI import VolumeSecurityGroupAPI

                # updating a VSG
                from NVMeshSDK.Entities.VolumeSecurityGroup import VolumeSecurityGroup
                from NVMeshSDK.MongoObj import MongoObj

                err, vsgs = VolumeSecurityGroupAPI.get(filter=[MongoObj(field=Key.Id, value="vsg1")])
                vsg1 = vsgs[0]
                >>> print vsg1
                {
                    "_id": "vsg1",
                    "description": "some description",
                    "keys": ["key1", "key2"],
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z")
                }

                setattr(vsg1, VolumeSecurityGroup.Description.dbKey, "VSG 1")
                vsg1.keys.append("key3")
                >>> print vsg1
                {
                    "_id": "vsg1",
                    "description": "VSG 1",
                    "keys": ["key1", "key2", "key3"],
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z")
                }


                volumeSecurityGroupAPI = VolumeSecurityGroupAPI()
                err, out = volumeSecurityGroupAPI.update([vsg1])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vsg1',
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
                        u'_id': u'vsg1',
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
        return super(VolumeSecurityGroupAPI, self).update(entitiesList=vsgs)

    def delete(self, vsgs):
        """**Delete VSGs**

        :param vsgs: list of VolumeSecurityGroup ids or VolumeSecurityGroup entities
        :type vsgs: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VolumeSecurityGroupAPI import VolumeSecurityGroupAPI

                # deleting 2 VSGs using their ids
                volumeSecurityGroupAPI = VolumeSecurityGroupAPI()
                err, out = volumeSecurityGroupAPI.delete(['vsg1','vsg2'])

                # deleting all the VSGs, first using the 'get' method to get all the VSGs
                # as VSG entities list then passing it to the 'delete' method
                err, currentVSGs = volumeSecurityGroupAPI.get()
                err, out = volumeSecurityGroupAPI.delete(currentVSGs)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vsg1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'vsg2',
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
                        u'_id': u'vsg1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'vsg2',
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
        return super(VolumeSecurityGroupAPI, self).delete(entitiesList=vsgs)

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return VolumeSecurityGroup
