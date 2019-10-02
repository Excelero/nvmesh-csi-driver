#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class BlockDevice(Entity):
    Id = AttributeRepresentation(display='Volume Name', dbKey='name')
    VolumeAttachmentStatus = AttributeRepresentation(display='Volume Attachments', dbKey='vol_status')
    IOEnabled = AttributeRepresentation(display='IO Enabled', dbKey='is_io_enabled')

    @Utils.initializer
    def __init__(self, is_io_enabled=None, io_perm=None, name=None, is_hidden=None, uuid=None, vol_status=None):
        pass