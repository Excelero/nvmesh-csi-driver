from NVMeshSDK.APIs.TargetClassAPI import TargetClassAPI
from NVMeshSDK.Entities.TargetClass import TargetClass
import TestBaseClass

import unittest


class TargetClassTest(TestBaseClass.TestBaseClass):

    def getEntitiesForSave(self):
        return [
            TargetClass(_id=u"tc2",
                servers=[],
                name=u"tc2",
                targetNodes=[
                    u"server-0.excelero.com"
                ]
            ),
            TargetClass(_id=u"tc3",
                servers=[],
                name=u"tc3",
                targetNodes=[
                    u"server-2.excelero.com"
                ]
            )]

    def getDbEntities(self):
        return [
            TargetClass(_id=u"tc0",
                        servers=[],
                        name=u"tc0",
                        targetNodes=[
                            u"server-0.excelero.com",
                            u"server-1.excelero.com"
                        ],
                        modifiedBy=u"admin@excelero.com",
                        createdBy=u"admin@excelero.com",
                        dateModified=u"2019-03-26T16:17:49.407Z",
                        dateCreated=u"2019-03-26T16:17:49.407Z"
                        ),
            TargetClass(_id=u"tc1",
                        servers=[],
                        name=u"tc1",
                        targetNodes=[
                            u"server-2.excelero.com",
                            u"server-3.excelero.com"
                        ],
                        modifiedBy=u"admin@excelero.com",
                        createdBy=u"admin@excelero.com",
                        dateModified=u"2019-03-26T16:17:57.056Z",
                        dateCreated=u"2019-03-26T16:17:57.056Z"
                        )
        ]

    def getApiUpdatePayload(self):
        tcs = self.getDbEntities()
        [setattr(tc, 'targetNodes', ['server-0.excelero.com']) for tc in tcs]
        return tcs

    @staticmethod
    def getAPI():
        return TargetClassAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
