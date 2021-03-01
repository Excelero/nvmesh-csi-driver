#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class DrivesStatus(Entity):
    Alarm = AttributeRepresentation(display='Alarm', dbKey='alarm')
    Critical = AttributeRepresentation(display='Critical', dbKey='critical')
    Healthy = AttributeRepresentation(display='Healthy', dbKey='healthy')

    @Utils.initializer
    def __init__(self, alarm=None, critical=None, healthy=None):
        pass
