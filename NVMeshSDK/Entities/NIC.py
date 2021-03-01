#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class NIC(Entity):
    Id = AttributeRepresentation(display='NIC ID', dbKey='nicID')
    MTU = AttributeRepresentation(display='MTU', dbKey='mtu')
    Status = AttributeRepresentation(display='Status', dbKey='status')
    Protocol = AttributeRepresentation(display='Protocol', dbKey='protocol')
    GUID = AttributeRepresentation(display='GUID', dbKey='guid')
    NodeID = AttributeRepresentation(display='Node ID', dbKey='nodeID')
    Health = AttributeRepresentation(display='Health', dbKey='health')
    DeviceType = AttributeRepresentation(display='Device Type', dbKey='deviceType')

    @Utils.initializer
    def __init__(self, status=None, pkey=None, nicID=None, mtu=None, version=None, pci_root=None, protocol=None, guid=None,
                 speed=None, nodeID=None, nodeUUID=None, uuid=None, health=None, missingCounter=None, deviceType=None):
        pass
