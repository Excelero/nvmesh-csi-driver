from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.Entities.Volume import Volume
from NVMeshSDK.Consts import RAIDLevels
import TestBaseClass

import unittest


class VolumeTest(TestBaseClass.TestBaseClass):

    def getEntitiesForSave(self):
        return [
            Volume(name="vol2",
                RAIDLevel=RAIDLevels.STRIPED_RAID_0,
                capacity="1g",
                description="Plain text",
                limitByNodes=["server-0.excelero.com", "server-1.excelero.com", "server-2.excelero.com"],
                stripeSize=32,
                stripeWidth=2,
            ),
            Volume(name="vol3",
                RAIDLevel=RAIDLevels.MIRRORED_RAID_1,
                capacity="10g",
                description="Plain text",
                numberOfMirrors=1
            ),
            Volume(name="vol4",
               RAIDLevel=RAIDLevels.JBOD,
               capacity="10g",
               description="Plain text",
               diskClasses=["dc0"]
            ),
            Volume(name="vol5",
               RAIDLevel=RAIDLevels.ERASURE_CODING,
               capacity="1g",
               description="Plain text",
               stripeSize=32,
               stripeWidth=1,
               dataBlocks=2,
               parityBlocks=1,
               protectionLevel="Full Separation"
            )
        ]

    def getDbEntities(self):
        return [
            Volume(_id=u"vol0",
                RAIDLevel=u"Concatenated",
                capacity=1000000000,
                limitByNodes=[],
                limitByDisks=[],
                serverClasses=[],
                diskClasses=[],
                relativeRebuildPriority=10,
                name=u"vol0",
                createdBy=u"admin@excelero.com",
                modifiedBy=u"admin@excelero.com",
                dateCreated=u"2019-03-26T16:16:14.004Z",
                dateModified=u"2019-03-26T16:16:13.993Z",
                version=1,
                isReserved=False,
                status=u"initializing",
                uuid=u"7a06f3f0-4fe2-11e9-850c-2b43004112a0",
                type=u"normal",
                health=u"healthy",
                lockServer={
                    u"maxNOwners":1,
                    u"type":2,
                    u"locksetShift":-1
                },
                chunks=[
                    {
                        u"_id" : u"7a087a90-4fe2-11e9-850c-2b43004112a0",
                        u"uuid" : u"7a087a90-4fe2-11e9-850c-2b43004112a0",
                        u"vlbs" : 0,
                        u"vlbe" : 244127,
                        u"pRaids" : [
                            {
                                u"activated" : False,
                                u"uuid" : u"7a087a92-4fe2-11e9-850c-2b43004112a0",
                                u"stripeIndex" : 0,
                                u"diskSegments" : [
                                    {
                                        u"_id" : u"7a087a91-4fe2-11e9-850c-2b43004112a0",
                                        u"uuid" : u"7a087a91-4fe2-11e9-850c-2b43004112a0",
                                        u"diskID" : u"server-0_drive_3.1",
                                        u"diskUUID" : u"a4d14de5-da57-459d-8d73-7eaf19829907",
                                        u"nodeUUID" : u"6ac7be00-4fde-11e9-850c-2b43004112a0",
                                        u"node_id" : u"server-0.excelero.com",
                                        u"volumeName" : u"vol0",
                                        u"volumeUUID" : u"7a06f3f0-4fe2-11e9-850c-2b43004112a0",
                                        u"pRaidUUID" : u"7a087a92-4fe2-11e9-850c-2b43004112a0",
                                        u"allocationIndex" : 0,
                                        u"pRaidIndex" : 0,
                                        u"lbs" : 1509440,
                                        u"lbe" : 1753567,
                                        u"type" : u"data",
                                        u"pRaidTypeIndex" : 0,
                                        u"status" : u"normal"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                blockSize=4096,
                blocks=244128
                ),
            Volume(_id=u"vol1",
                RAIDLevel=u"Mirrored RAID-1",
                numberOfMirrors=1,
                capacity=1000000000,
                limitByNodes=[],
                limitByDisks=[],
                serverClasses=[],
                diskClasses=[],
                relativeRebuildPriority=10,
                name=u"vol1",
                createdBy=u"admin@excelero.com",
                modifiedBy=u"admin@excelero.com",
                dateCreated=u"2019-03-26T16:16:21.795Z",
                dateModified=u"2019-03-26T16:16:21.774Z",
                version=1,
                isReserved=False,
                status=u"initializing",
                uuid=u"7eab75c0-4fe2-11e9-850c-2b43004112a0",
                type=u"normal",
                health=u"healthy",
                lockServer={
                    u"maxNOwners":2,
                    u"type":2,
                    u"locksetShift":-1
                },
                chunks=[
                    {
                        u"_id" : u"7eb1b750-4fe2-11e9-850c-2b43004112a0",
                        u"uuid" : u"7eb1b750-4fe2-11e9-850c-2b43004112a0",
                        u"vlbs" : 0,
                        u"vlbe" : 244127,
                        u"pRaids" : [
                            {
                                u"activated" : False,
                                u"uuid" : u"7eb1b752-4fe2-11e9-850c-2b43004112a0",
                                u"stripeIndex" : 0,
                                u"diskSegments" : [
                                    {
                                        u"_id" : u"7eb1b751-4fe2-11e9-850c-2b43004112a0",
                                        u"uuid" : u"7eb1b751-4fe2-11e9-850c-2b43004112a0",
                                        u"diskID" : u"server-3_drive_3.1",
                                        u"diskUUID" : u"098a628f-1b3c-4fbd-bc34-b6371ce2a233",
                                        u"nodeUUID" : u"6c8f3790-4fde-11e9-850c-2b43004112a0",
                                        u"node_id" : u"server-3.excelero.com",
                                        u"volumeName" : u"vol1",
                                        u"volumeUUID" : u"7eab75c0-4fe2-11e9-850c-2b43004112a0",
                                        u"pRaidUUID" : u"7eb1b752-4fe2-11e9-850c-2b43004112a0",
                                        u"allocationIndex" : 0,
                                        u"pRaidIndex" : 0,
                                        u"lbs" : 1509440,
                                        u"lbe" : 1753567,
                                        u"type" : "data",
                                        u"pRaidTypeIndex" : 0,
                                        u"status" : "normal"
                                    },
                                    {
                                        u"_id" : u"7eb27aa0-4fe2-11e9-850c-2b43004112a0",
                                        u"uuid" : u"7eb27aa0-4fe2-11e9-850c-2b43004112a0",
                                        u"diskID" : u"server-2_drive_3.1",
                                        u"diskUUID" : u"3d3b8fef-552a-4c48-8df7-a0f06239ef75",
                                        u"nodeUUID" : u"6bf9d560-4fde-11e9-850c-2b43004112a0",
                                        u"node_id" : u"server-2.excelero.com",
                                        u"volumeName" : u"vol1",
                                        u"volumeUUID" : u"7eab75c0-4fe2-11e9-850c-2b43004112a0",
                                        u"pRaidUUID" : u"7eb1b752-4fe2-11e9-850c-2b43004112a0",
                                        u"allocationIndex" : 1,
                                        u"pRaidIndex" : 1,
                                        u"lbs" : 1509440,
                                        u"lbe" : 1753567,
                                        u"type" : "data",
                                        u"pRaidTypeIndex" : 1,
                                        u"status" : "normal"
                                    },
                                    {
                                        u"_id" : u"7eb2c8c0-4fe2-11e9-850c-2b43004112a0",
                                        u"uuid" : u"7eb2c8c0-4fe2-11e9-850c-2b43004112a0",
                                        u"diskID" : u"server-0_drive_0.1",
                                        u"diskUUID" : u"eecea2fb-7968-4260-93f3-2fad7169405b",
                                        u"nodeUUID" : u"6ac7be00-4fde-11e9-850c-2b43004112a0",
                                        u"node_id" : u"server-0.excelero.com",
                                        u"volumeName" : u"vol1",
                                        u"volumeUUID" : u"7eab75c0-4fe2-11e9-850c-2b43004112a0",
                                        u"pRaidUUID" : u"7eb1b752-4fe2-11e9-850c-2b43004112a0",
                                        u"allocationIndex" : 2,
                                        u"pRaidIndex" : 2,
                                        u"lbs" : 0,
                                        u"lbe" : 0,
                                        u"type" : u"raftonly",
                                        u"pRaidTypeIndex" : 0,
                                        u"status" : u"normal"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                blockSize=4096,
                blocks=244128
                )
        ]

    def testSave(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForSave(), payload={'isReserved': False})
        err, apiRes = self.myAPI.save(self.getEntitiesForSave())
        self.assertIsNone(err, 'err: {0}'.format(err))
        self.assertListEqual(apiRes, expectedRes, 'Failed {0} in: {1}, result: {2}'.format(self._testMethodName, self.className, apiRes))

    def getApiUpdatePayload(self):
        volumes = self.getDbEntities()
        [setattr(volume, 'capacity', '20g') for volume in volumes]
        return volumes

    def testRebuild(self):
        # tests that the success is false
        expectedRes = self.getExpectedResultObj(entities=self.getDbEntities(), success=False)
        err, apiRes = self.myAPI.rebuildVolumes(self.getDbEntities())
        self.checkResults(expectedRes, err, apiRes)

    @staticmethod
    def getAPI():
        return VolumeAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
