#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class NIC(Entity):
    Id = AttributeRepresentation(display='NIC ID', dbKey='nicID')

    @Utils.initializer
    def __init__(self, status=None, pkey=None, nicID=None, mtu=None, version=None, pci_root=None, protocol=None, guid=None,
                 speed=None, nodeID=None, nodeUUID=None, uuid=None, health=None, missingCounter=None, deviceType=None):
        pass
