from NVMeshSDK.Entities.VPG import VPG
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class VpgAPI(BaseClassAPI):
    endpointRoute = EndpointRoutes.VPGS

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        """**Get VPGs limit the result using filter, sort and projection**

        :param filter: Filter before fetching using MongoDB filter objects, defaults to None
        :type filter: list, optional
        :param sort: Sort before fetching using MongoDB filter objects, defaults to None
        :type sort: list, optional
        :param projection: Project before fetching using MongoDB filter objects, defaults to None
        :type projection: list, optional
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: list of VPG entities
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VpgAPI import VpgAPI

                # fetching all the VPGs and projecting only some attributes using MongoObj and VPG class attributes
                from NVMeshSDK.Entities.VPG import VPG
                from NVMeshSDK.MongoObj import MongoObj

                vpgAPI = VpgAPI()

                myProj = [MongoObj(field=VPG.Id, value=1), MongoObj(field=VPG.Size, value=1), MongoObj(field=VPG.RaidLevel, value=1)]
                err, out = vpgAPI.get(projection=myProj)

                >>> err
                None
                >>> for vpg in out: print vpg
                {
                    "RAIDLevel": "Concatenated",
                    "_id": "DEFAULT_CONCATENATED_VPG",
                    "capacity": 0,
                    "name": "DEFAULT_CONCATENATED_VPG"
                }
                {
                    "RAIDLevel": "Striped RAID-0",
                    "_id": "DEFAULT_RAID_0_VPG",
                    "capacity": 0,
                    "name": "DEFAULT_RAID_0_VPG"
                }
                {
                    "RAIDLevel": "Mirrored RAID-1",
                    "_id": "DEFAULT_RAID_1_VPG",
                    "capacity": 0,
                    "name": "DEFAULT_RAID_1_VPG"
                {
                    "RAIDLevel": "Striped & Mirrored RAID-10",
                    "_id": "DEFAULT_RAID_10_VPG",
                    "capacity": 0,
                    "name": "DEFAULT_RAID_10_VPG"
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
        return super(VpgAPI, self).get(page=page, count=count, filter=filter, sort=sort, projection=projection)

    def delete(self, vpgs):
        """**Delete VPGs**

        :param vpgs: list of vpg ids or VPG entities
        :type vpgs: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VpgAPI import VpgAPI

                # deleting 2 VPGs using their ids
                vpgAPI = VpgAPI()
                err, out = vpgAPI.delete(['vpg1', 'vpg2'])

                # deleting all VPGs, first using the 'get' method to get all the VPGs
                # as VPG entities list then passing it to the 'delete' method
                err, currentVPGs = vpgAPI.get()
                err, out = vpgAPI.delete(currentVPGs)

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'vpg1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'vpg2',
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
                        u'_id': u'vpg1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'vpg2',
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
        return super(VpgAPI, self).delete(entitiesList=vpgs)

    def save(self, vpgs):
        """**Save VPGs**

        :param vpgs: list of VPG entities
        :type vpgs: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.VpgAPI import VpgAPI

                # creating 2 VPGs using the VPG entity
                from NVMeshSDK.Entities.VPG import VPG

                vpg1 = VPG(name="vol1", RAIDLevel="Mirrored RAID-1", capacity=1024**3, numberOfMirrors=1)
                vpg2 = VPG(name="vol2", RAIDLevel="Concatenated", capacity=1024**3, description="some description")

                vpgAPI =VpgAPI()
                err, out = vpgAPI.save([vol1, vol2])

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
        return super(VpgAPI, self).save(entitiesList=vpgs)

    def update(self, vpgs):
        return super(VpgAPI, self).update(entitiesList=vpgs)

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return VPG
