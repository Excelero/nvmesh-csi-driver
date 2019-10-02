#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.DiskSegment import DiskSegment
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class PRAID(Entity):
    DiskSegments = AttributeRepresentation(display='Drive Segments', dbKey='diskSegments', type=DiskSegment)
    __objectsToInstantiate = ['DiskSegments']

    @Utils.initializer
    def __init__(self, activated=None, version=None, uuid=None, stripeIndex=None, diskSegments=None, tomaLeaderConnectionSequence=None,
                 tomaLeaderRaftTerm=None):
        pass

    def getObjectsToInstantiate(self):
        return PRAID.__objectsToInstantiate
