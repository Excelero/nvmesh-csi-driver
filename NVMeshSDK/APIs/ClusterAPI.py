from NVMeshSDK.Entities.ClusterStatus import ClusterStatus
from .BaseClassAPI import BaseClassAPI
from NVMeshSDK.Consts import EndpointRoutes


class ClusterAPI(BaseClassAPI):

    endpointRoute = EndpointRoutes.INDEX

    def status(self):
        """**Get status query of the system.**

        :return: cluster status entity
        :rtype: ClusterStatus

        - Example::

            from NVMeshSDK.APIs.ClusterAPI import ClusterAPI

            clusterAPI = ClusterAPI()
            err, out = clusterAPI.status()

            >>> err
            None
            >>> print out
            {
                "managementVersion": "1.3.2-2",
                "servers": {
                    "totalServers": 12,
                    "offlineServers": 1,
                    "timedOutServers": 12
                },
                "clients": {
                    "timedOutClients": 4,
                    "offlineClients": 1,
                    "totalClients": 4
                },
                "volumes": {
                    "Striped RAID-0": 4,
                    "Mirrored RAID-1": 7,
                    "Concatenated": 7
                },
                "totalSpace": 12002647080000,
                "allocatedSpace": 3420001664064,
                "freeSpace": 8582645415936,
                "errors": [
                    {
                        "message": "Drive: CVCQ524600A2400AGN.1 is missing",
                        "timestamp": "2015-08-18T13:01:11.691Z",
                        "meta": {
                            "header": "Disk failure"
                        }
                    },
                    {
                        "message": "Nic: 0xfe80000000000000f452140300798461 is missing",
                        "timestamp": "2015-08-18T13:01:11.692Z",
                        "meta": {
                            "header": "NIC failure"
                        }
                    }
                ],
                "warnings": []
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
        routes = ['status']

        err, out = self.makeGet(routes)

        if out is not None:
            status = self.getType()(**out)
            status.deserialize()
            return None, status
        else:
            return err, None

    def shutDownClusterNodes(self):
        """**Shut down cluster nodes. --Start the shut down process**

        :return: tuple (err, out)

            **err**: HTTP error details or None if there were no errors

            **out**: operation success details per entity or None if there was an HTTP error
        :rtype: (dict, list)

        - Example::

                from NVMeshSDK.APIs.ClusterAPI import ClusterAPI

                clusterAPI = ClusterAPI()
                err, out = clusterAPI.shutdownClusterNodes()

           - Expected Success Response::

               >>> err
               None

               >>> out
               {
                   u'_id': None,
                   u'error': None,
                   u'payload': 'The cluster shutdown process started',
                   u'success': True
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

        controlJob = {'control': 'shutdownAll'}
        return self.makePost(routes=['cluster', 'shutDownCluster'], objects=controlJob)

    def get(self, page=0, count=0, filter=None, sort=None, projection=None):
        raise NotImplemented

    def delete(self, clients):
        raise NotImplemented

    def save(self, entitiesList):
        raise NotImplemented

    def update(self, entitiesList):
        raise NotImplemented

    def count(self):
        raise NotImplemented

    @classmethod
    def getEndpointRoute(cls):
        return cls.endpointRoute

    def getType(self):
        return ClusterStatus