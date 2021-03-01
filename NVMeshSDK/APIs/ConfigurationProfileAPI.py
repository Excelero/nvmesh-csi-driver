from NVMeshSDK.Entities.ConfigurationProfile import ConfigurationProfile
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class ConfigurationProfileAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.CONFIGURATION_PROFILE

    def get(self, page=0, count=0, projection=None, filter=None, sort=None):
        """**Get configuration profile by page and count, limit the result using filter, sort and projection**

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

            **out**: list of ConfigurationProfile entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ConfigurationProfileAPI import ConfigurationProfileAPI

                # fetching all configuration profiles
                configProfileAPI = ConfigurationProfileAPI()
                err, out = configProfileAPI.get()

                >>> err
                None
                >>> for configProfile in out: print  configProfile
                {
                    "_id": "Cluster Default",
                    "config": {
                        "AGENT_LOGGING_LEVEL": "INFO",
                        "AUTO_ATTACH_VOLUMES": true,
                        "DUMP_FTRACE_ON_OOPS": false,
                        "IPV4_ONLY": true,
                        "MANAGEMENT_PROTOCOL": "https",
                        "MCS_LOGGING_LEVEL": "INFO",
                        "MLX5_RDDA_ENABLED": true
                    },
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-10-30T14:08:36.777Z",
                    "dateModified": "2019-10-30T14:08:36.777Z",
                    "deleteNotAllowed": true,
                    "editNotAllowed": false,
                    "hosts": [],
                    "labels": [],
                    "modifiedBy": "admin@excelero.com",
                    "name": "Cluster Default",
                    "uuid": "cluster_default",
                    "version": 1
                }
                {
                    "_id": "NVMesh Debug",
                    "config": {
                        "AGENT_LOGGING_LEVEL": "DEBUG",
                        "DUMP_FTRACE_ON_OOPS": true,
                        "MCS_LOGGING_LEVEL": "DEBUG",
                        "TOMA_BUILD_TYPE": "Verbose"
                    },
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-10-30T14:08:36.778Z",
                    "dateModified": "2019-10-30T14:08:36.778Z",
                    "deleteNotAllowed": true,
                    "editNotAllowed": false,
                    "hosts": [],
                    "labels": [],
                    "modifiedBy": "admin@excelero.com",
                    "name": "NVMesh Debug",
                    "uuid": "nvmesh_debug",
                    "version": 1
                }
                {
                    "_id": "NVMesh Default",
                    "config": {
                        "AGENT_LOGGING_LEVEL": "INFO",
                        "AUTO_ATTACH_VOLUMES": true,
                        "DUMP_FTRACE_ON_OOPS": false,
                        "IPV4_ONLY": true,
                        "MANAGEMENT_PROTOCOL": "https",
                        "MCS_LOGGING_LEVEL": "INFO",
                        "MLX5_RDDA_ENABLED": true
                    },
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-10-30T14:08:36.777Z",
                    "dateModified": "2019-10-30T14:08:36.777Z",
                    "deleteNotAllowed": true,
                    "editNotAllowed": true,
                    "hosts": [],
                    "labels": [],
                    "modifiedBy": "admin@excelero.com",
                    "name": "NVMesh Default",
                    "uuid": "nvmesh_default",
                    "version": 1
                }

                # fetching all configuration profiles and projecting only the id and version of each profile using MongoObj and ConfigurationProfile class attributes
                from NVMeshSDK.Entities.ConfigurationProfile import ConfigurationProfile
                from NVMeshSDK.MongoObj import MongoObj
                err, out = configProfileAPI.get(projection=[MongoObj(field=ConfigurationProfile.Version, value=1), MongoObj(field=ConfigurationProfile.Id, value=1)])

                >>> err
                None
                >>> for configProfile in out: print  configProfile
                {
                    "_id": "Cluster Default",
                    "version": 1
                }
                {
                    "_id": "NVMesh Debug",
                    "version": 1
                }
                {
                    "_id": "NVMesh Default",
                    "version": 1
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
        return super(ConfigurationProfileAPI, self).get(page=page, count=count, projection=projection, filter=filter, sort=sort)

    def save(self, configProfiles):
        """**Save configuration profiles**

        :param configProfiles: list of ConfigurationProfile entities
        :type configProfiles: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ConfigurationProfileAPI import ConfigurationProfileAPI

                # creating 2 configuration profiles
                from NVMeshSDK.Entities.ConfigurationProfile import ConfigurationProfile
                p1 = ConfigurationProfile(name="My Profile", config={})
                p2 = ConfigurationProfile(name="My Profile 2", config={"MCS_LOGGING_LEVEL": "DEBUG"})

                configProfileAPI = ConfigurationProfileAPI()
                err, out = configProfileAPI.save([p1, p2])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'My Profile',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'My Profile 2',
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
                        u'_id': u'My Profile',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'My Profile 2',
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

        return self.makePost(['save'], configProfiles)

    def update(self, configProfiles):
        """**Update configuration profiles**

        :param configProfiles: list of ConfigurationProfile entities
        :type configProfiles: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                # updating a profile
                from NVMeshSDK.APIs.ConfigurationProfileAPI import ConfigurationProfileAPI
                from NVMeshSDK.Entities.ConfigurationProfile import ConfigurationProfile
                from NVMeshSDK.MongoObj import MongoObj

                configProfileAPI = ConfigurationProfileAPI()
                err, profiles = configProfileAPI.get(filter=[MongoObj(field=ConfigurationProfile.Id, value="Cluster Default")])
                clusterDefaultProfile = profiles[0]

                clusterDefaultProfile.config["AUTO_ATTACH_VOLUMES"] = False

                >>> print clusterDefaultProfile
                {
                    "_id": "Cluster Default",
                    "config": {
                        "AGENT_LOGGING_LEVEL": "INFO",
                        "AUTO_ATTACH_VOLUMES": false,
                        "DUMP_FTRACE_ON_OOPS": false,
                        "IPV4_ONLY": true,
                        "MANAGEMENT_PROTOCOL": "https",
                        "MCS_LOGGING_LEVEL": "INFO",
                        "MLX5_RDDA_ENABLED": true
                    },
                    "createdBy": "admin@excelero.com",
                    "dateCreated": "2019-11-01T08:19:47.243Z",
                    "dateModified": "2019-11-01T08:19:47.243Z",
                    "deleteNotAllowed": true,
                    "description": null,
                    "editNotAllowed": false,
                    "hosts": [],
                    "labels": [],
                    "modifiedBy": "admin@excelero.com",
                    "name": "Cluster Default",
                    "uuid": "cluster_default",
                    "version": 1
                }



                err, out = configProfileAPI.update([clusterDefaultProfile])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'Cluster Default',
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
                        u'_id': u'Cluster Default',
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
        return super(ConfigurationProfileAPI, self).update(entitiesList=configProfiles)

    def delete(self, configProfiles):
        """**Delete configuration profile**

        :param configProfiles: list of configuration Profile ids or ConfigurationProfile entities
        :type configProfiles: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ConfigurationProfileAPI import ConfigurationProfileAPI

                configProfileAPI = ConfigurationProfileAPI()
                err, out = configProfileAPI.delete(['p1','p2'])

                # deleting all configuration Profiles, first using the 'get' method to get all the profiles
                # as ConfigurationProfile entities list then passing it to the 'delete' method
                # Note that profiles that are locked for deletion will return an error

                err, profiles = configProfileAPI.get()
                err, out = configProfileAPI.delete(profiles)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                   {
                      u      '_id':u      'Cluster Default',
                      u      'error':u      'deleting this Profile is not allowed',
                      u      'payload':None,
                      u      'success':False
                   },
                   {
                      u      '_id':u      'NVMesh Debug',
                      u      'error':u      'deleting this Profile is not allowed',
                      u      'payload':None,
                      u      'success':False
                   },
                   {
                      u      '_id':u      'NVMesh Default',
                      u      'error':u      'deleting this Profile is not allowed',
                      u      'payload':None,
                      u      'success':False
                   },
                   {
                      u      '_id':u      'My Profile 2',
                      u      'error':None,
                      u      'payload':None,
                      u      'success':True
                   },
                   {
                      u      '_id':u      'My Profile',
                      u      'error':None,
                      u      'payload':None,
                      u      'success':True
                   }
                ]

            - Expected Operation Fail Response::

                >>> err
                None

                >>> out
                [
                   {
                      u      '_id':u      'Cluster Default',
                      u      'error':u      'deleting this Profile is not allowed',
                      u      'payload':None,
                      u      'success':False
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
        return super(ConfigurationProfileAPI, self).delete(entitiesList=configProfiles)

    def count(self):
        return super(ConfigurationProfileAPI, self).count()

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return ConfigurationProfile
