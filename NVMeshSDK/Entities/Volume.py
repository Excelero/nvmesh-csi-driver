#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.Chunk import Chunk
from NVMeshSDK.Entities.Reservation import Reservation
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Volume(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Health
            * Description
            * Status
            * RaidLevel
            * ParityBlocks
            * DataBlocks
            * Protection
            * Size
            * StripeWidth
            * TargetClasses
            * DriveClasses
            * Domain
            * RelativeRebuildPriority
            * Chunks
            * Reservation
            * IgnoreNodeSeparation
            * SelectedClientsForNvmf
            * EnableNVMf
            * EnableCrcCheck
            * VSGs
    """
    Id = AttributeRepresentation(display='Name', dbKey='name')
    Health = AttributeRepresentation(display='Health', dbKey='health')
    Description = AttributeRepresentation(display='Description', dbKey='description')
    Status = AttributeRepresentation(display='Status', dbKey='status')
    RaidLevel = AttributeRepresentation(display='RAID Level', dbKey='RAIDLevel')
    ParityBlocks = AttributeRepresentation(display='Parity', dbKey='parityBlocks')
    DataBlocks = AttributeRepresentation(display='Data', dbKey='dataBlocks')
    Protection = AttributeRepresentation(display='Protection Level', dbKey='protectionLevel')
    Size = AttributeRepresentation(display='Size', dbKey='capacity')
    StripeWidth = AttributeRepresentation(display='Stripe Width', dbKey='stripeWidth')
    TargetClasses = AttributeRepresentation(display='Target Classes', dbKey='serverClasses')
    DriveClasses = AttributeRepresentation(display='Drive Classes', dbKey='diskClasses')
    Domain = AttributeRepresentation(display='Domain', dbKey='domain')
    RelativeRebuildPriority = AttributeRepresentation(display='Relative Rebuild Priority', dbKey='relativeRebuildPriority')
    Chunks = AttributeRepresentation(display='Chunks', dbKey='chunks', type=Chunk)
    Reservation = AttributeRepresentation(display='Reservation', dbKey='reservation', type=Reservation)
    IgnoreNodeSeparation = AttributeRepresentation(display='Ignore Node Separation', dbKey='ignoreNodeSeparation')
    SelectedClientsForNvmf = AttributeRepresentation(display='Clients Allowed To Export Via NVMf', dbKey='selectedClientsForNvmf')
    EnableNVMf = AttributeRepresentation(display='Access Via NVMf', dbKey='enableNVMf')
    Action = AttributeRepresentation(display='Action', dbKey='action')
    EnableCrcCheck = AttributeRepresentation(display='Enable CRC Check', dbKey='enableCrcCheck')
    LimitByDrive = AttributeRepresentation(display='Limit by drives', dbKey='limitByDisks')
    LimitByTarget = AttributeRepresentation(display='Limit by targets', dbKey='limitByNodes')
    VSGs = AttributeRepresentation(display='VSGs', dbKey='VSGs')
    __objectsToInstantiate = ['Chunks', 'Reservation']

    @Utils.initializer
    def __init__(self, name=None, RAIDLevel=None, capacity=None, VPG=None, _id=None, relativeRebuildPriority=None, description=None, diskClasses=None, serverClasses=None,
                 limitByDisks=None, limitByNodes=None, numberOfMirrors=None, createdBy=None, modifiedBy=None, dateModified=None, dateCreated=None, isReserved=None,
                 status=None, blocks=None, chunks=None, stripeSize=None, stripeWidth=None, dataBlocks=None, parityBlocks=None, protectionLevel=None, domain=None,
                 uuid=None, blockSize=None, version=None, type=None, health=None, lockServer=None, reservation=None, ignoreNodeSeparation=None, selectedClientsForNvmf=None,
                 enableNVMf=None, action=None, enableCrcCheck=None, VSGs=None, use_debug_di=None):
        """**Initializes volume entity**

                :param name: the name of the volume
                :type name: str, optional
                :param RAIDLevel: the RAID level of the volume, options: Concatenated, Striped RAID-0, Mirrored RAID-1, Striped & Mirrored RAID-10, Erasure Coding.
                :type RAIDLevel: str, optional
                :param capacity: space to allocate for the volume, use 'MAX' for using all of the available space.
                :type capacity: int or str, optional
                :param VPG: the VPG to use
                :type VPG: str, optional
                :param relativeRebuildPriority: sets the volume relative rebuild priority, defaults to None
                :type relativeRebuildPriority: int, optional
                :param description: description of the volume, defaults to None
                :type description: str, optional
                :param diskClasses: limit volume allocation to specific diskClasses, defaults to None
                :type diskClasses: list, optional
                :param serverClasses: limit volume allocation to specific serverClasses, defaults to None
                :type serverClasses: list, optional
                :param limitByDisks: limit volume allocation to specific disks, defaults to None
                :type limitByDisks: list, optional
                :param limitByNodes: limit volume allocation to specific nodes, defaults to None
                :type limitByNodes: list, optional
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
                :param ignoreNodeSeparation: when True node separation will be ignored for a mirrored volume (No Target Redundancy), defaults to None
                :type ignoreNodeSeparation: bool, optional
                :param selectedClientsForNvmf: clients that allowed to export via NVMf, defaults to None
                :type selectedClientsForNvmf: list, optional
                :param enableNVMf: enables access to the NVMesh volume using the NVMf protocol, defaults to None
                :type enableNVMf: bool, optional
                :param enableCrcCheck: enables CRC check, defaults to None
                :type enableCrcCheck: bool, optional
                :param VSGs: associated volume security groups, defaults to None
                :type VSGs: list, optional
        """
        if hasattr(self, 'name'):
            self._id = self.name

    def getObjectsToInstantiate(self):
        return Volume.__objectsToInstantiate

    @staticmethod
    def getSchemaName():
        return 'volumeEntity'
