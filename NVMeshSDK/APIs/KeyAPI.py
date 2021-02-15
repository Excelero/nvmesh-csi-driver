from NVMeshSDK.Entities.Key import Key
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class KeyAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.KEYS

    def get(self, page=0, count=0, projection=None, filter=None, sort=None):
        """**Get keys by page and count, limit the result using filter, sort and projection**

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

            **out**: list of Key entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.KeyAPI import KeyAPI

                # fetching all the keys
                keyAPI = KeyAPI()
                err, out = keyAPI.get()

                >>> err
                None
                >>> for key in out: print key
                {
                    "_id": "KeyA",
                    "uuid": "1ca95530-4bc8-11e5-b932-53542b263b32"
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z")
                }
                {
                    "_id": "KeyB",
                    "uuid": "1ca95530-4bc8-11e5-b932-53542b263b31"
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
        return super(KeyAPI, self).get(page=page, count=count, projection=projection, filter=filter, sort=sort)

    def save(self, keys):
        """**Save keys**

        :param keys: list of Key entities
        :type keys: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.KeyAPI import KeyAPI

                # creating 2 keys using the Key entity
                from NVMeshSDK.Entities.Key import Key
                key1 = Key(_id="key1", description="Key 1")
                key2 = Key(_id="key2", description="Key 2")

                keyAPI = KeyAPI()
                err, out = keyAPI.save([key1, key2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'key1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'key2',
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
                        u'_id': u'key1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'key2',
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
        return super(KeyAPI, self).save(entitiesList=keys)

    def update(self, keys):
        """**Update keys**

        :param keys: list of Key entities
        :type keys: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.KeyAPI import KeyAPI

                # updating a key
                from NVMeshSDK.Entities.Key import Key
                from NVMeshSDK.MongoObj import MongoObj

                err, keys = keyAPI.get(filter=[MongoObj(field=Key.Id, value="key1")])
                key1 = keys[0]
                >>> print key1
                {
                    "_id": "key1",
                    "uuid": "1ca95530-4bc8-11e5-b932-53542b263b32"
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z")
                }

                setattr(key1, Key.Description.dbKey, "secure key")
                >>> print key1
                {
                    "_id": "key1",
                    "uuid": "1ca95530-4bc8-11e5-b932-53542b263b32"
                    "createdBy" : "tomzan@mail.com",
                    "modifiedBy" : "tomzan@mail.com",
                    "dateCreated" : ISODate("2015-08-19T17:02:54.136Z"),
                    "dateModified" : ISODate("2015-08-19T17:02:54.136Z"),
                    "description": "secure key"
                }


                keyAPI = KeyAPI()
                err, out = keyAPI.update([key1])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'key1',
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
                        u'_id': u'key1',
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
        return super(KeyAPI, self).update(entitiesList=keys)

    def delete(self, keys):
        """**Delete keys**

        :param keys: list of key ids or Key entities
        :type keys: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.KeyAPI import KeyAPI

                # deleting 2 keys using their ids
                keyAPI = KeyAPI()
                err, out = keyAPI.delete(['key1','key2'])

                # deleting all the keys, first using the 'get' method to get all the keys
                # as keys entities list then passing it to the 'delete' method
                err, currentKeys = keyAPI.get()
                err, out = keyAPI.delete(currentKeys)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'key1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'key2',
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
                        u'_id': u'key1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'key2',
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
        return super(KeyAPI, self).delete(entitiesList=keys)

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return Key
