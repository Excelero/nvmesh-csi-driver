#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class VolumeLayout(Entity):
    ChunkNumber = AttributeRepresentation(display='Chunk', dbKey='chunkNumber')
    StripeNumber = AttributeRepresentation(display='Stripe', dbKey='stripeNumber')
    SegmentNumber = AttributeRepresentation(display='Segment', dbKey='segmentNumber')
    SegmentType = AttributeRepresentation(display='Segment Type', dbKey='segmentType')
    LBAStart = AttributeRepresentation(display='LBA Start', dbKey='lbaStart')
    LBAEnd = AttributeRepresentation(display='LBA End', dbKey='lbaEnd')
    Status = AttributeRepresentation(display='Segment Status', dbKey='status')
    DriveID = AttributeRepresentation(display='Drive Serial', dbKey='drive')
    TargetID = AttributeRepresentation(display='Target', dbKey='target')

    @Utils.initializer
    def __init__(self, chunkNumber=None, stripeNumber=None, segmentNumber=None, segmentType=None, lbaStart=None,
                 lbaEnd=None, status=None, drive=None, target=None):
        pass