from NVMeshSDK.Entities.Target import Target
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class DriveAPI(BaseClassAPI):
    """**All the functions of the Drive API are defined here**"""

    endpointRoute = EndpointRoutes.DISKS

    # entity or id
    def deleteDrives(self, drives):
        """**Delete drives. --Drive can only be deleted if it doesn't contain any diskSegments and not in NOT_INITIALIZED status or in EXCLUDED state**

        :param drives: list of drives ids or Drive entities
        :type drives: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveAPI import DriveAPI

                # deleting 2 drives using their ids
                driveAPI = DriveAPI()
                err, out = driveAPI.deleteDrives(['PHMD614200A3400FGN.1', 'S23YNAAH200330.1'])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'PHMD614200A3400FGN.1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'S23YNAAH200330.1',
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
                        u'_id': u'PHMD614200A3400FGN.1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'S23YNAAH200330.1',
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
        return self.makePost(routes=['delete'], objects={'Ids': self.getEntityIds(drives, idAttr='diskID')})

    # entity or id
    def evictDrives(self, drives):
        """**Evict drives**

        :param drives: list of drives ids or Drive entities
        :type drives: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveAPI import DriveAPI

                # evicting 2 drives using their ids
                driveAPI = DriveAPI()
                err, out = driveAPI.evictDrives(['PHMD614200A3400FGN.1', 'S23YNAAH200330.1'])

            - Expected Success Response::

                >>> err
                None

                >>> out
                [
                    {
                        u'_id': u'PHMD614200A3400FGN.1',
                        u'error': None,
                        u'payload': None,
                        u'success': True
                    },
                    {
                        u'_id': u'S23YNAAH200330.1',
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
                        u'_id': u'PHMD614200A3400FGN.1',
                        u'error': <Failure Reason>,
                        u'payload': None,
                        u'success': False
                    },
                    {
                        u'_id': u'S23YNAAH200330.1',
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
        return self.makePost(routes=['evictDiskByDiskIds'], objects={'Ids': self.getEntityIds(drives, idAttr='diskID')})

    # entity or id
    def formatDrives(self, drives, formatType=None):
        """**Format drives. --Start the format process for the specified disks according to the specified format type**

        :param drives: list of drives ids or Drive entities
        :type drives: list
        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.DriveAPI import DriveAPI

                # formatting 2 drives using their ids
                driveAPI = DriveAPI()
                err, out = driveAPI.formatDrives(['PHMD614200A3400FGN.1', 'S23YNAAH200330.1'])

           - Expected Success Response::

               >>> err
               None

               >>> out
               [
                   {
                       u'_id': u'PHMD614200A3400FGN.1',
                       u'error': None,
                       u'payload': None,
                       u'success': True
                   },
                   {
                       u'_id': u'S23YNAAH200330.1',
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
                       u'_id': u'PHMD614200A3400FGN.1',
                       u'error': <Failure Reason>,
                       u'payload': None,
                       u'success': False
                   },
                   {
                       u'_id': u'S23YNAAH200330.1',
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
        driveIds = self.getEntityIds(drives, idAttr='diskID')
        payload = {'diskIDs': driveIds}

        if formatType is not None:
            payload.update({'formatType': formatType})

        return self.makePost(routes=['formatDiskByDiskIds'], objects=payload)

    def save(self, entitiesList):
        raise NotImplemented

    def update(self, entitiesList):
        raise NotImplemented

    def delete(self, entitiesList):
        return self.deleteDrives(drives=entitiesList)

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return Target