#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class TargetsStatus(Entity):
    Total = AttributeRepresentation(display='Total', dbKey='totalServers')
    Offline = AttributeRepresentation(display='Offline', dbKey='offlineServers')
    TimedOut = AttributeRepresentation(display='Timed Out', dbKey='timedOutServers')

    @Utils.initializer
    def __init__(self, totalServers=None, offlineServers=None, timedOutServers=None):
        pass
