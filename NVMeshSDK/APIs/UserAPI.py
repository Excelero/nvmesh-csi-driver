from NVMeshSDK.Entities.User import User
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class UserAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.USERS

    def get(self, filter=None, sort=None):
        """**Get users, limit the result using filter and sort**

        :param filter: Filter before fetching using MongoDB filter objects, defaults to None
        :type filter: list, optional
        :param sort: Sort before fetching using MongoDB filter objects, defaults to None
        :type sort: list, optional
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: list of User entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.UserAPI import UserAPI

                # fetching all the users
                userAPI = UserAPI()
                err, out = userAPI.get()

                >>> err
                None
                >>> for user in out: print user
                {
                    "_id": "admin@excelero.com",
                    "dateCreated": "2019-07-09T12:58:30.450Z",
                    "email": "admin@excelero.com",
                    "eulaDateOfSignature": "2019-07-09T12:59:20.209Z",
                    "eulaSignature": "dhd",
                    "hasAcceptedEula": true,
                    "layout": {
                        "settings": {
                            "isControlPanelPinned": true,
                            "rollupPolicy": {
                                "samplingDuration": "2min",
                                "samplingRate": "1s"
                            }
                        },
                        "statistics": {...}
                    },
                    "notificationLevel": "NONE",
                    "relogin": false,
                    "role": "Admin"
                }
                {
                    "_id": "ron@excelero.com",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-10T07:52:18.608Z",
                    "dateModified": "2019-07-10T07:52:18.608Z",
                    "email": "ron@excelero.com",
                    "layout": {
                        "statistics": {...}
                    },
                    "modifiedBy": "admin@excelero.com",
                    "notificationLevel": "NONE",
                    "relogin": false,
                    "role": "Observer"
                }

                # fetching all users and filtering by role using MongoObj and User's class attribute
                from NVMeshSDK.Entities.User import User
                from NVMeshSDK.MongoObj import MongoObj
                err, out = userAPI.get(filter=[MongoObj(field=User.Role, value='Observer')])

                >>> err
                None
                >>> for user in out: print user
                {
                    "_id": "ron@excelero.com",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-10T07:52:18.608Z",
                    "dateModified": "2019-07-10T07:52:18.608Z",
                    "email": "ron@excelero.com",
                    "layout": {
                        "statistics": {...}
                    },
                    "modifiedBy": "admin@excelero.com",
                    "notificationLevel": "NONE",
                    "relogin": false,
                    "role": "Observer"
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
        return super(UserAPI, self).get(page=None, count=None, filter=filter, sort=sort)

    def save(self, users):
        """**Save users**

        :param users: list of User entities
        :type users: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.UserAPI import UserAPI

                # creating a user using a User entity
                from NVMeshSDK.Entities.User import User

                user1 = User(email="joe@excelero.com", role="Admin", notificationLevel="NONE", password="verySecure", confirmationPassword="verySecure")

                userAPI = UserAPI()
                err, out = userAPI.save([user1])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'joe@excelero.com',
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
                        u'_id': u'joe@excelero.com',
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
        return super(UserAPI, self).save(entitiesList=users)

    def delete(self, users):
        """**Delete users**

        :param users: list of User entities (only email attribute is needed)
        :type users: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.UserAPI import UserAPI

                # deleting a user using the User entity, first using the 'get' method to get the specific user
                #  as a User entity then passing it to the delete method
                from NVMeshSDK.Entities.User import User
                from NVMeshSDK.MongoObj import MongoObj

                err, out = userAPI.get(filter=[MongoObj(field=User.Email, value='joe@excelero.com')])
                joeUser = out[0]
                err, out = userAPI.delete([joeUser])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'joe@excelero.com',
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
                        u'_id': u'joe@excelero.com',
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
        return super(UserAPI, self).delete(entitiesList=users)

    def update(self, users):
        """**Update users**

        :param driveClasses: list of User entities
        :type driveClasses: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.UserAPI import UserAPI

                # updating a user
                from NVMeshSDK.Entities.User import User
                from NVMeshSDK.MongoObj import MongoObj

                err, users = userAPI.get(filter=[MongoObj(field=User.Email, value="ron@excelero.com")])
                ronUser = users[0]
                >>> print ronUser
                {
                    "_id": "ron@excelero.com",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-10T07:52:18.608Z",
                    "dateModified": "2019-07-10T11:27:23.848Z",
                    "email": "ron@excelero.com",
                    "layout": {
                        "statistics": {...}
                    },
                    "modifiedBy": "app@excelero.com",
                    "notificationLevel": "NONE",
                    "relogin": false,
                    "role": "Observer"
                }


                ronUser.role = "Admin"
                >>> print ronUser
                {
                    "_id": "ron@excelero.com",
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-07-10T07:52:18.608Z",
                    "dateModified": "2019-07-10T11:27:23.848Z",
                    "email": "ron@excelero.com",
                    "layout": {
                        "statistics": {...}
                    },
                    "modifiedBy": "app@excelero.com",
                    "notificationLevel": "NONE",
                    "relogin": false,
                    "role": "Admin"
                }


                usersAPI = UserAPI()
                err, out = userAPI.update([ronUser])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'ron@excelero.com',
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
                        u'_id': u'ron@excelero.com',
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
        return super(UserAPI, self).update(entitiesList=users)

    def resetPassword(self, users):
        """**Reset users passwords**

        :param users: list of User entities
        :type users: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.UserAPI import UserAPI

                # resetting all users passwords
                err, allUsers = userAPI.get()

                userAPI = UserAPI()
                err, out = userAPI.resetPassword(allUsers)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'joe@excelero.com',
                        u'error': None,
                        u'payload': {u'newPassword': u'ecbbi'},
                        u'success': True
                    },
                    {
                        u'_id': u'ron@excelero.com',
                        u'error': None,
                        u'payload': {u'newPassword': u'abba4'},
                        u'success': True
                    }
                ]


            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'joe@excelero.com',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'ron@excelero.com',
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
        for user in users:
            user.resetPassword = True

        return self.makePost(['update'], users)

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return User