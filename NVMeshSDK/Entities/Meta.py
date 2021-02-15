#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.Link import Link
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Meta(Entity):
    Header = AttributeRepresentation(display='Header', dbKey='header')
    Acknowledged = AttributeRepresentation(display='Acknowledged', dbKey='acknowledged')
    RawMessage = AttributeRepresentation(display='Message', dbKey='rawMessage')
    Link = AttributeRepresentation(display='', dbKey='link', type=Link)
    __objectsToInstantiate = ['Link']

    @Utils.initializer
    def __init__(self, header=None, acknowledged=None, rawMessage=None, link=None):
        pass

    def getObjectsToInstantiate(self):
        return Meta.__objectsToInstantiate