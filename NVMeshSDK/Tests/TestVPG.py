from NVMeshSDK.APIs.VpgAPI import VpgAPI
from NVMeshSDK.Entities.VPG import VPG
import TestBaseClass

import unittest


class VPGTest(TestBaseClass.TestBaseClass):

    def getEntitiesForSave(self):
        return [
            VPG(_id=u"vpg2",
                    diskClasses=[],
                    name=u"vpg2",
                    serverClasses=[u'tc0'],
                    RAIDLevel=u"Concatenated",
                    serviceResources=u"RDDA",
                    capacity=1000000000,
                    relativeRebuildPriority=10,
                    modifiedBy=u"admin@excelero.com",
                    createdBy=u"admin@excelero.com",
                    dateModified=u"2019-03-27T08:54:07.961Z",
                    dateCreated=u"2019-03-27T08:54:07.961Z"
                ),
            VPG(_id=u"vpg3",
                    diskClasses=[],
                    name=u"vpg3",
                    serverClasses=[],
                    RAIDLevel=u"Mirrored RAID-1",
                    numberOfMirrors=1,
                    serviceResources=u"RDDA",
                    capacity=5000000000,
                    relativeRebuildPriority=10,
                    modifiedBy=u"admin@excelero.com",
                    createdBy=u"admin@excelero.com",
                    dateModified=u"2019-03-27T08:54:07.961Z",
                    dateCreated=u"2019-03-27T08:54:07.961Z"
                )
        ]

    def getDbEntities(self):
        return [
            VPG(_id=u"vpg0",
                    diskClasses=[],
                    name=u"vpg0",
                    serverClasses=[],
                    RAIDLevel=u"Concatenated",
                    serviceResources=u"RDDA",
                    capacity=1000000000,
                    relativeRebuildPriority=10,
                    modifiedBy=u"admin@excelero.com",
                    createdBy=u"admin@excelero.com",
                    dateModified=u"2019-03-27T08:54:07.961Z",
                    dateCreated=u"2019-03-27T08:54:07.961Z"
                ),
            VPG(_id=u"vpg1",
                    diskClasses=[],
                    name=u"vpg1",
                    serverClasses=[],
                    RAIDLevel=u"Mirrored RAID-1",
                    numberOfMirrors=1,
                    serviceResources=u"RDDA",
                    capacity=1000000000,
                    relativeRebuildPriority=10,
                    modifiedBy=u"admin@excelero.com",
                    createdBy=u"admin@excelero.com",
                    dateModified=u"2019-03-27T08:54:07.961Z",
                    dateCreated=u"2019-03-27T08:54:07.961Z"
                )
        ]

    def testSave(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForSave(), payload={'isReserved': True})
        err, apiRes = self.myAPI.save(self.getEntitiesForSave())
        self.checkResults(expectedRes, err, apiRes)

    @unittest.skipIf(True, 'Not Implemented')
    def test10Update(self):
        pass

    @staticmethod
    def getAPI():
        return VpgAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
