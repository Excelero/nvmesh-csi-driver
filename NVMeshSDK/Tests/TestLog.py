from NVMeshSDK.APIs.LogAPI import LogAPI
from NVMeshSDK.Entities.Log import Log
import TestBaseClass

import unittest


class LogTest(TestBaseClass.TestBaseClass):
    NUMBER_OF_EXPECTED_LOGS = 3
    NUMBER_OF_EXPECTED_ALERTS = 1

    def getDbEntities(self):
        return [
            Log(_id=u"5c9a497bc4fe0e25bb7369e7",
                timestamp=u"2019-03-26T15:47:07.418Z",
                level=u"INFO",
                message=u"New client: client-1.excelero.com",
                meta={
                    u"header": u"New client",
                    u"link": {
                        u"entityType": u"CLIENT",
                        u"entityText": u"client-1.excelero.com"
                    },
                    u"acknowledged": False,
                    u"rawMessage": u"New client: {}"
                }
            ),
            Log(_id=u"5c9a497cc4fe0e25bb7369e8",
                timestamp=u"2019-03-26T15:47:08.399Z",
                level=u"INFO",
                message=u"New client: client-2.excelero.com",
                meta={
                    u"header": u"New client",
                    u"link": {
                        u"entityType": u"CLIENT",
                        u"entityText": u"client-2.excelero.com"
                    },
                    u"acknowledged": False,
                    u"rawMessage": u"New client: {}"
                }
            )
        ] + self.getDbAlert()

    def getDbAlert(self):
        return [
            Log(
                _id=u"5c988591cb75831de89bf2c5",
                timestamp=u"2019-03-25T07:38:57.973Z",
                level=u"ERROR",
                message=u"Drive: drive_100 reported status: Ok and health: critical",
                meta={
                    u"header": u"Drive failure",
                    u"link": {
                        u"entityType": u"DISK",
                        u"entityText": u"S3HCNX0K500667.1",
                        u"target": u"server-0.excelero.com"
                    },
                    u"acknowledged": False,
                    u"rawMessage": u"Drive: {} reported status: Ok and health: critical"
                }
            )
        ]

    def test11AcknowledgeAll(self):

        err, apiRes = self.myAPI.acknowledgeAll()
        self.checkResults(self.getApiSuccessObj(), err, apiRes, apiAssert=self.assertDictEqual)

    def test10Acknowledge(self):
        def filterAlert(log):
            return log.level != 'ERROR'

        logs = self.getDbEntities()
        logs = filter(filterAlert, logs) # filter the alert - will be acked in the AckAll test
        apiResults = self.myAPI.acknowledgeLogs(logs)
        expectedResults = self.getExpectedResultObj(entities=logs)
        for apiRes, expectedRes in list(zip(apiResults, expectedResults)):
            self.checkResults(expectedRes, err=apiRes[0], apiRes=apiRes[1], apiAssert=self.assertDictEqual)

    def test01GetAlerts(self):
        expextedRes = self.getDbAlert()
        apiRes = self.myAPI.getAlerts()
        self.checkResults(expextedRes, err=None, apiRes=apiRes)

    def test05Count(self):
        err, apiRes = self.myAPI.count()
        self.checkResults(self.NUMBER_OF_EXPECTED_LOGS, err, apiRes, apiAssert=self.assertEqual)

    def test05CountAlerts(self):
        err, apiRes = self.myAPI.countAlerts()
        self.checkResults(self.NUMBER_OF_EXPECTED_ALERTS, err, apiRes, apiAssert=self.assertEqual)

    @unittest.skipIf(True, 'Not Implemented')
    def testSave(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def test10Update(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def testDelete(self):
        pass

    @staticmethod
    def getAPI():
        return LogAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
