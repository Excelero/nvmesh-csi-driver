#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.MongoDBMember import MongoDBMember
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class MongoDB(Entity):
    """
    Static class attributes.
            * Set
            * Members
    """
    Set = AttributeRepresentation(display='Replica Set', dbKey='set')
    Members = AttributeRepresentation(display='Members', dbKey='members', type=MongoDBMember)
    __objectsToInstantiate = ['Members']



    @Utils.initializer
    def __init__(self, set=None, members=None):
        """**Initializes MongoDB entity**

        :param set: MongoDB replica set name, defaults to None
        :type set: str, optional
        :param members: cluster members, defaults to None
        :type members: list, optional
        """

        pass

    def getObjectsToInstantiate(self):
        return MongoDB.__objectsToInstantiate