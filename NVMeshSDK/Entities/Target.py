#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.Drive import Drive
from NVMeshSDK.Entities.NIC import NIC
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Target(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Drives
            * Nics
            * Version
            * Health
            * TomaStatus
    """
    Id = AttributeRepresentation(display='Name', dbKey='node_id')
    Drives = AttributeRepresentation(display='Drives', dbKey='disks', type=Drive)
    Nics = AttributeRepresentation(display='NICs', dbKey='nics', type=NIC)
    Version = AttributeRepresentation(display='Version', dbKey='version')
    Health = AttributeRepresentation(display='Health', dbKey='health')
    TomaStatus = AttributeRepresentation(display='TOMA Status', dbKey='tomaStatus')
    __objectsToInstantiate = ['Drives', 'Nics']



    @Utils.initializer
    def __init__(self, _id=None, branch=None, disks=None, nics=None, node_status=None, version=None, node_id=None,
                 commit=None, messageSequence=None, connectionSequence=None, dateModified=None, health=None,
                 cpu_load=None, cpu_temp=None, uuid=None, tomaStatus=None, wsStatus=None):
        """**Initializes target entity**

        :param _id: target's id, defaults to None
        :type _id: str, optional
        :param disks: target's drives, defaults to None
        :type disks: list, optional
        :param nics: target's nics, defaults to None
        :type nics: list, optional
        :param node_status: target's status, defaults to None
        :type node_status: int, optional
        :param version: management version, defaults to None
        :type version: str, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        :param health: target's health, defaults to None
        :type health: str, optional
        """

        pass

    def getObjectsToInstantiate(self):
        return Target.__objectsToInstantiate

    @staticmethod
    def getSchemaName():
        return 'targetEntity'