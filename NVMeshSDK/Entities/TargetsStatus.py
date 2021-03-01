#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class TargetsStatus(Entity):
    Total = AttributeRepresentation(display='Total', dbKey='totalServers')
    Offline = AttributeRepresentation(display='Offline', dbKey='offlineServers')
    TimedOut = AttributeRepresentation(display='Timed Out', dbKey='timedOutServers')
    Alarm = AttributeRepresentation(display='Alarm', dbKey='alarm')
    Critical = AttributeRepresentation(display='Critical', dbKey='critical')
    Healthy = AttributeRepresentation(display='Healthy', dbKey='healthy')

    @Utils.initializer
    def __init__(self, totalServers=None, offlineServers=None, timedOutServers=None, alarm=None, critical=None, healthy=None):
        pass
