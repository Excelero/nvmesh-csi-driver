#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class DiskSegment(Entity):
    NodeID = AttributeRepresentation(display='Target', dbKey='node_id')
    DriveID = AttributeRepresentation(display='Drive', dbKey='diskID')
    DirtyBits = AttributeRepresentation(display='Dirty Bits', dbKey='remainingDirtyBits')
    LBS = AttributeRepresentation(display='lbs', dbKey='lbs')
    LBE = AttributeRepresentation(display='lbe', dbKey='lbe')
    Type = AttributeRepresentation(display='Segment Type', dbKey='type')
    Status = AttributeRepresentation(display='Status', dbKey='status')


    @Utils.initializer
    def __init__(self, _id=None, uuid=None, diskID=None, diskUUID=None, nodeUUID=None, node_id=None, volumeName=None,
                 volumeUUID=None, pRaidUUID=None, allocationIndex=None, pRaidIndex=None, lbs=None, lbe=None, type=None,
                 pRaidTypeIndex=None, status=None, remainingDirtyBits=None, isExtension=None):
        pass

