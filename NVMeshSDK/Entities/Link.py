#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Link(Entity):
    EntityType = AttributeRepresentation(display='', dbKey='entityType')
    EntityText = AttributeRepresentation(display='', dbKey='entityText')

    @Utils.initializer
    def __init__(self, entityType=None, entityText=None):
        pass
