#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.PRAID import PRAID
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Chunk(Entity):
    Id = AttributeRepresentation(display='Name', dbKey='_id')
    VLBS = AttributeRepresentation(display='vlbs', dbKey='vlbs')
    VLBE = AttributeRepresentation(display='vlbe', dbKey='vlbe')
    PRAIDS = AttributeRepresentation(display='pRaids', dbKey='pRaids', type=PRAID)
    __objectsToInstantiate = ['PRAIDS']

    @Utils.initializer
    def __init__(self, _id=None, uuid=None, vlbs=None, vlbe=None, pRaids=None):
        pass

    def getObjectsToInstantiate(self):
        return Chunk.__objectsToInstantiate
