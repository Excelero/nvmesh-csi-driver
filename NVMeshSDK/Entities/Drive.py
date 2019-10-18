#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Drive(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Model
            * Status
            * NodeID
            * Vendor
            * BlockSize
            * MetadataSize
            * Health
            * Excluded
            * Evicted
            * UsableBlocks
            * AvailableBlocks
    """
    Id = AttributeRepresentation(display='Serial Number', dbKey='diskID')
    Model = AttributeRepresentation(display='Model', dbKey='Model')
    Status = AttributeRepresentation(display='Status', dbKey='status')
    NodeID = AttributeRepresentation(display='Target', dbKey='nodeID')
    Vendor = AttributeRepresentation(display='Vendor', dbKey='Vendor')
    BlockSize = AttributeRepresentation(display='Block Size', dbKey='block_size')
    MetadataSize = AttributeRepresentation(display='Metadata Size', dbKey='metadata_size')
    Health = AttributeRepresentation(display='Health', dbKey='health')
    Excluded = AttributeRepresentation(display='Excluded', dbKey='isExcluded')
    Evicted = AttributeRepresentation(display='Evicted', dbKey='isOutOfService')
    UsableBlocks = AttributeRepresentation(display='Usable Blocks', dbKey='usableBlocks')
    AvailableBlocks = AttributeRepresentation(display='Available Blocks', dbKey='availableBlocks')


    @Utils.initializer
    def __init__(self, Completion_Queues=None, writeCounter=None, Available_Spare=None, isExcluded=None, MSIX_Interrupts=None, GPT=None,
                 pci_address=None, Percentage_Used=None, block_size=None, Controller_Busy_Time=None, Vendor=None, Available_Spare_Threshold=None,
                 reappearingCounter=None, metadata_size=None, Numa_Node=None, activeFormatRequestCounter=None, Number_of_Error_Information_Log_Entries=None,
                 Serial_Number=None, Unsafe_Shutdowns=None, diskID=None, status=None, blocks=None, Media_Errors=None, Power_Cycles=None, formatRequestCounter=None,
                 Model=None, Submission_Queues=None, Power_On_Hours=None, formatOptions=None, Critical_Warning=None, lastReportDiskVersion=None,
                 vendorID=None, nodeID=None, nodeUUID=None, uuid=None, availableBlocks=None, usableBlocks=None, largestSegmentAvailable=None, version=None,
                 health=None, diskSegments=None, pci_root=None, isPendingFormat=None, zeroWriteCounter=None, nZeroedBlks=None, metadataCapabilities=None,
                 writeCounterAtFormat=None, reappearingOutOfSync=None, isOutOfService=None, formatInProgress=None):

        """**Initializes drive entity**
        """
        pass
