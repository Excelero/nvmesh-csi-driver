from NVMeshSDK.APIs.DriveClassAPI import DriveClassAPI
from NVMeshSDK.Entities.DriveClass import DriveClass
from NVMeshSDK.Entities.Drive import Drive
import TestBaseClass

import unittest


class DriveClassTest(TestBaseClass.TestBaseClass):

    def getEntitiesForSave(self):
        return [
            DriveClass(_id=u"dc2",
                disks=[
                    Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_1"),
                    Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_5")
                ]
            ),
            DriveClass(_id=u"dc3",
                disks=[
                    Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_1"),
                    Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_5")
                ]
            )]

    def getDbEntities(self):
        return [
            DriveClass(_id=u"dc0",
                        tags=[],
                        disks=[
                            Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_1"),
                            Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_4")
                        ],
                        modifiedBy=u"admin@excelero.com",
                        createdBy=u"admin@excelero.com",
                        dateModified=u"2019-05-01T14:35:17.923Z",
                        dateCreated=u"2019-05-01T14:35:17.923Z"
                        ),
            DriveClass(_id=u"dc1",
                        tags=[],
                        disks=[
                            Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_7"),
                            Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_11")
                        ],
                        modifiedBy=u"admin@excelero.com",
                        createdBy=u"admin@excelero.com",
                        dateModified=u"2019-05-01T14:36:27.204Z",
                        dateCreated=u"2019-05-01T14:36:27.204Z"
                        )
        ]

    def getApiUpdatePayload(self):
        dcs = self.getDbEntities()
        [setattr(dc, 'disks', [Drive(model=u"SAMSUNG MZWLL800HEHP-00000______________", diskID=u"drive_8")]) for dc in dcs]
        return dcs

    @staticmethod
    def getAPI():
        return DriveClassAPI()


if __name__ == '__main__':
    unittest.main(verbosity=2)
