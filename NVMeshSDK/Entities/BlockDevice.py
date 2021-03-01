#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.Reservation import Reservation
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class BlockDevice(Entity):
    Id = AttributeRepresentation(display='Volume Name', dbKey='name')
    VolumeAttachmentStatus = AttributeRepresentation(display='Volume Attachments', dbKey='vol_status')
    IOEnabled = AttributeRepresentation(display='IO Enabled', dbKey='ioEnabled')
    IsIOEnabled = AttributeRepresentation(display='IO Enabled', dbKey='is_io_enabled')
    IOPerm = AttributeRepresentation(display='IO Enabled', dbKey='io_perm')
    Reservation = AttributeRepresentation(display='Reservation', dbKey='reservation', type=Reservation)
    __objectsToInstantiate = ['Reservation']

    @Utils.initializer
    def __init__(self, is_io_enabled=None, ioEnabled=None, io_perm=None, name=None, is_hidden=None, uuid=None, vol_status=None, reservation=None):
        pass

    def getObjectsToInstantiate(self):
        return BlockDevice.__objectsToInstantiate