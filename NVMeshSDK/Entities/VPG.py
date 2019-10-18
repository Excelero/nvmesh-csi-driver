#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class VPG(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Description
            * RaidLevel
            * Size
    """
    Id = AttributeRepresentation(display='Name', dbKey='name')
    Size = AttributeRepresentation(display='Reserved Space', dbKey='capacity')
    Description = AttributeRepresentation(display='Description', dbKey='description')
    RaidLevel = AttributeRepresentation(display='RAID Level', dbKey='RAIDLevel')

    @Utils.initializer
    def __init__(self, name=None, RAIDLevel=None, capacity=None, VPG=None, _id=None, relativeRebuildPriority=None, description=None, diskClasses=None, serverClasses=None,
                 limitByDisks=None, limitByNodes=None, numberOfMirrors=None, createdBy=None, modifiedBy=None, dateModified=None, dateCreated=None, isReserved=None,
                 status=None, blocks=None, chunks=None, stripeSize=None, stripeWidth=None, dataBlocks=None, parityBlocks=None, protectionLevel=None, domain=None,
                 uuid=None, blockSize=None, version=None, type=None, health=None, lockServer=None, serviceResources=None, isDefault=None):
        """**Initializes VPG entity**

                :param name: the name of the VPG
                :type name: str, optional
                :param RAIDLevel: the RAID level of the VPG, options: Concatenated, Striped RAID-0, Mirrored RAID-1, Striped & Mirrored RAID-10, Erasure Coding.
                :type RAIDLevel: str, optional
                :param capacity: space to allocate for the VPG
                :type capacity: int, optional
                :param VPG: the VPG to use
                :type VPG: str, optional
                :param description: description of the VPG, defaults to None
                :type description: str, optional
                :param diskClasses: limit volume allocation to specific diskClasses, defaults to None
                :type diskClasses: list, optional
                :param serverClasses: limit volume allocation to specific serverClasses, defaults to None
                :type serverClasses: list, optional
                :param numberOfMirrors: number of mirrors to use, required if RAIDLevel is Mirrored RAID-1 or Striped & Mirrored RAID-10., defaults to None
                :type numberOfMirrors: int, optional
                :param stripeSize: number in blocks of 4k, i.e. stripeSize:32 = 128k, required if RAIDLevel is Striped RAID-0 or Striped & Mirrored RAID-10 or Erasure Coding, optional, defaults to None
                :type stripeSize: str, optional
                :param stripeWidth: number of disks to use, required if RAIDLevel is Striped RAID-0 or Striped & Mirrored RAID-10, defaults to None
                :type stripeWidth: int, optional
                :param dataBlocks: number of disks to use, required if RAIDLevel is Erasure Coding, defaults to None
                :type dataBlocks: int, optional
                :param parityBlocks: number of disks to use, required if RAIDLevel is Erasure Coding, defaults to None
                :type parityBlocks: int, optional
                :param protectionLevel: protection level to use, defaults to None
                :type protectionLevel: str, optional
                :param domain: the domain of the volume, defaults to None
                :type domain: str, optional
                :param health: volume's health, defaults to None
                :type health: str, optional
                :param status: the status of the volume, defaults to None
                :type status: int, optional
        """

        if hasattr(self, '_id'):
                self.name = self._id

    @staticmethod
    def getSchemaName():
        return 'vpgEntity'
