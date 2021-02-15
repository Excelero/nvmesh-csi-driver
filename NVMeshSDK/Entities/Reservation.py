#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Reservation(Entity):
    Mode = AttributeRepresentation(display='Reservation Mode', dbKey='mode')
    Version = AttributeRepresentation(display='Reservation Version', dbKey='version')
    ReservedBy = AttributeRepresentation(display='Reserved By', dbKey='reservedBy')

    @Utils.initializer
    def __init__(self, mode=None, version=None, reservedBy=None):
        pass
