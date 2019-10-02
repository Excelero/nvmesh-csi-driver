from NVMeshSDK.APIs.DriveAPI import DriveAPI
from NVMeshSDK.Entities.Drive import Drive
import TestBaseClass

import unittest


class DriveTest(TestBaseClass.TestBaseClass):
    DRIVE_FOR_FORMAT_AND_EVICT = 100

    def getDbEntities(self):
        return [
            Drive(diskID=u"drive_0"),
            Drive(diskID=u"drive_1"),
            Drive(diskID=u"drive_2"),
        ]

    def getDriveForFormatAndDelete(self):
        return [
            Drive(diskID=u"drive_100")
        ]

    def testDelete(self):
        # expecting a delete failure because all of the drives are in use
        expectedRes = self.getExpectedResultObj(entities=self.getDbEntities(), idAttr='diskID', success=False, error=u"disk is in use, can't delete")
        err, apiRes = self.myAPI.deleteDrives(self.getDbEntities())
        self.checkResults(expectedRes, err, apiRes)

    def testFormat(self):
        expectedRes = self.getExpectedResultObj(entities=self.getDriveForFormatAndDelete(), idAttr='diskID')
        err, apiRes = self.myAPI.formatDrives(self.getDriveForFormatAndDelete())
        self.checkResults(expectedRes, err, apiRes)

    def testEvict(self):
        expectedRes = self.getExpectedResultObj(entities=self.getDriveForFormatAndDelete(), idAttr='diskID')
        err, apiRes = self.myAPI.evictDrives(self.getDriveForFormatAndDelete())
        self.checkResults(expectedRes, err, apiRes)

    @unittest.skipIf(True, 'Not Implemented')
    def test00Get(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def testSave(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def test10Update(self):
        pass

    @staticmethod
    def getAPI():
        return DriveAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
