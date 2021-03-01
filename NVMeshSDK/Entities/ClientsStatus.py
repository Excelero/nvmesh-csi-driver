#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class ClientsStatus(Entity):
    Total = AttributeRepresentation(display='Total', dbKey='totalClients')
    Offline = AttributeRepresentation(display='Offline', dbKey='offlineClients')
    TimedOut = AttributeRepresentation(display='Timed Out', dbKey='timedOutClients')
    Alarm = AttributeRepresentation(display='Alarm', dbKey='alarm')
    Critical = AttributeRepresentation(display='Critical', dbKey='critical')
    Healthy = AttributeRepresentation(display='Healthy', dbKey='healthy')

    @Utils.initializer
    def __init__(self, totalClients=None, offlineClients=None, timedOutClients=None,  alarm=None, critical=None, healthy=None):
        pass
