#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class ClientsStatus(Entity):
    Total = AttributeRepresentation(display='Total', dbKey='totalClients')
    Offline = AttributeRepresentation(display='Offline', dbKey='offlineClients')
    TimedOut = AttributeRepresentation(display='Timed Out', dbKey='timedOutClients')

    @Utils.initializer
    def __init__(self, totalClients=None, offlineClients=None, timedOutClients=None):
        pass
