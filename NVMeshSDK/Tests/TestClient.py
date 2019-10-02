from NVMeshSDK.APIs.ClientAPI import ClientAPI
from NVMeshSDK.Entities.Client import Client
import TestBaseClass

import unittest


class ClientTest(TestBaseClass.TestBaseClass):
    NUMBER_OF_EXPECTED_CLIENTS = 2
    VOLUME_FOR_ATTACH_DETACH = 'vol1'

    def getDbEntities(self):
        return [
            Client(_id=u"client-0.excelero.com",
                        block_devices=[],
                        clientID=u"client-0.excelero.com",
                        client_status=1,
                        configuration_version=-1,
                        messageSequence=247,
                        connectionSequence=1,
                        dateModified=u"2019-03-26T15:53:54.907Z",
                        health=u"healthy",
                        health_old=u"healthy"
                        ),
            Client(_id=u"client-1.excelero.com",
                        block_devices=[],
                        clientID=u"client-1.excelero.com",
                        client_status=1,
                        configuration_version=-1,
                        messageSequence=248,
                        connectionSequence=1,
                        dateModified=u"2019-03-26T15:53:55.910Z",
                        health=u"healthy",
                        health_old=u"healthy"
                        )
        ]

    def test05Count(self):
        err, apiRes = self.myAPI.count()
        self.checkResults(self.NUMBER_OF_EXPECTED_CLIENTS, err, apiRes, apiAssert=self.assertEqual)

    def test02Attach(self):
        err, apiRes = self.myAPI.attach(volumes=[self.VOLUME_FOR_ATTACH_DETACH], client=self.getDbEntities()[1])
        expectedRes = [{u"success": True, u"_id": 'vol1', u"error": None, u"payload": None}]
        self.checkResults(expectedRes, err, apiRes)

    def test01Detach(self):
        apiAttachSuccess = self.myAPI.attach(volumes=[self.VOLUME_FOR_ATTACH_DETACH], client=self.getDbEntities()[0])[1][0]['success']
        self.assertTrue(apiAttachSuccess, 'Unable to attach the volume before detach')

        err, apiRes = self.myAPI.detach(volumes=[self.VOLUME_FOR_ATTACH_DETACH], client=self.getDbEntities()[0])
        expectedRes = [{u"success": True, u"_id": 'vol1', u"error": None, u"payload": None}]
        self.checkResults(expectedRes, err, apiRes)

    @unittest.skipIf(True, 'Not Implemented')
    def testSave(self):
        pass

    @unittest.skipIf(True, 'Not Implemented')
    def test10Update(self):
        pass

    @staticmethod
    def getAPI():
        return ClientAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
