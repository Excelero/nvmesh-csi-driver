from NVMeshSDK.APIs.TargetAPI import TargetAPI
from NVMeshSDK.Entities.Target import Target
import TestBaseClass

import unittest


class TargetTest(TestBaseClass.TestBaseClass):
    NUMBER_OF_EXPECTED_TARGETS = 5

    def getTargetForDelete(self):
        return [
            Target(
                    _id=u"server-4.excelero.com_00",
                    dateModified=u"2019-04-01T12:31:25.445Z",
                    disks=[
                        {
                            u"diskID": u"server-4_drive_0.1"
                        },
                        {
                            u"diskID": u"server-4_drive_1.1"
                        },
                        {
                            u"diskID": u"server-4_drive_2.1"
                        },
                        {
                            u"diskID": u"server-4_drive_3.1"
                        }
                    ],
                    health=u"healthy",
                    nics=[
                        {
                            u"nicID": u"a05e54b7-4a02-46f9-8597-d408aaf6d6cf"
                        },
                        {
                            u"nicID": u"81e59f57-142c-4c04-9e02-c4ada657a096"
                        }
                    ],
                    node_id=u"server-4.excelero.com",
                    node_status=1,
                    tomaStatus=u"up",
                    version=u"2.0.0-4134"
            )
        ]

    def getDbEntities(self):
        return [
            Target(_id=u"server-0.excelero.com_00",
                        version=u'2.0.0-4134',
                        node_id=u"server-0.excelero.com",
                        nics= [{u'nicID': u'dd746c26-11b3-458a-909e-67a436392946'},
                            {u'nicID': u'27c41a5a-bfeb-40f4-90db-9a4eb35b5246'}],
                        disks=[{u'diskID': u'drive_0'}, {u'diskID': u'drive_1'}, {u'diskID': u'drive_2'},
                                         {u'diskID': u'drive_3'}, {u'diskID': u'drive_100'}],
                        tomaStatus=u'up',
                        node_status=1,
                        dateModified=u"2019-03-26T15:53:58.946Z",
                        health=u"healthy"
                        ),
            Target(_id=u"server-1.excelero.com_00",
                       version=u'2.0.0-4134',
                       node_id=u"server-1.excelero.com",
                       nics=[{u'nicID': u'25a3d849-92c5-4a16-b665-3775470bcb57'},
                             {u'nicID': u'2d99e863-20c6-4895-a35e-f758e5e49ae1'}],
                       disks=[{u'diskID': u'drive_4'}, {u'diskID': u'drive_5'}, {u'diskID': u'drive_6'},
                              {u'diskID': u'drive_7'}],
                       tomaStatus=u'up',
                       node_status=1,
                       dateModified=u"2019-03-26T15:53:59.947Z",
                       health=u"healthy"
                       ),
            Target(_id=u"server-2.excelero.com_00",
                        version=u'2.0.0-4134',
                        node_id=u"server-2.excelero.com",
                        nics= [{u'nicID': u'fe4b0e21-c0a5-49a1-a61a-4a4de9b56f59'},
                                                                   {u'nicID': u'18178757-ff65-4f36-bd07-140e00b0fcc5'}],
                        disks=[{u'diskID': u'drive_8'}, {u'diskID': u'drive_9'}, {u'diskID': u'drive_10'},
                                         {u'diskID': u'drive_11'}],
                        tomaStatus=u'up',
                        node_status=1,
                        dateModified=u"2019-03-26T15:54:00.955Z",
                        health=u"healthy"
                        ),
            Target(_id=u"server-3.excelero.com_00",
                       version=u'2.0.0-4134',
                       node_id=u"server-3.excelero.com",
                       nics=[{u'nicID': u'a25c6ba3-4756-480d-b357-adf6e3c08f98'},
                                                                       {u'nicID': u'45c526f4-ccee-4f2e-90c0-ebc7c2f0caf9'}],
                       disks=[{u'diskID': u'drive_12'}, {u'diskID': u'drive_13'}, {u'diskID': u'drive_14'},
                                             {u'diskID': u'drive_15'}],
                       tomaStatus=u'up',
                       node_status=1,
                       dateModified=u"2019-03-26T15:54:01.953Z",
                       health=u"healthy"
                   )
        ] + self.getTargetForDelete()

    def test05Count(self):
        err, apiRes = self.myAPI.count()
        self.checkResults(self.NUMBER_OF_EXPECTED_TARGETS, err, apiRes, apiAssert=self.assertEqual)

    def testDelete(self):
        expectedRes = self.getExpectedResultObj(entities=self.getTargetForDelete(), idAttr='node_id')
        err, apiRes = self.myAPI.delete(self.getTargetForDelete())
        self.checkResults(expectedRes, err, apiRes)

    def testShutdownAll(self):
        expectedRes = self.getApiSuccessObj(_id='shutdownAll', success=True)
        err, apiRes = self.myAPI.shutdownAll()
        self.checkResults(expectedRes, err, apiRes, apiAssert=self.assertDictEqual)

    @unittest.skipIf(True, 'Not Implemented')
    def testSave(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def test10Update(self):
        pass

    @staticmethod
    def getAPI():
        return TargetAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
