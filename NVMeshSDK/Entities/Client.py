#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation
from NVMeshSDK.Entities.BlockDevice import BlockDevice


class Client(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Version
            * Health
            * BlockDevices
    """

    Id = AttributeRepresentation(display='Name', dbKey='_id')
    Version = AttributeRepresentation(display='Version', dbKey='version')
    Health = AttributeRepresentation(display='Health', dbKey='health')
    Status = AttributeRepresentation(display='Status', dbKey='client_status')
    NVMfAttachedVolumes = AttributeRepresentation(display='NVMf Attached Volumes', dbKey='nvmfAttachedVolumes')
    BlockDevices = AttributeRepresentation(display='Volume Attachments', dbKey='block_devices', type=BlockDevice)
    __objectsToInstantiate = ['BlockDevices']

    @Utils.initializer
    def __init__(self, _id=None, branch=None, configuration_version=None, client_status=None, block_devices=None, version=None, client_id=None, controlJobs=None,
                 commit=None, messageSequence=None, connectionSequence=None, dateModified=None, health=None, health_old=None, managementAgentStatus=None, nvmfAttachedVolumes=None):
                """**Initializes client entity**

                    :param _id: client's id, defaults to None
                    :type _id: str, optional
                    :param client_status: client's status, defaults to None
                    :type client_status: int, optional
                    :param block_devices: client's block devices, defaults to None
                    :type block_devices: list, optional
                    :param version: management version, defaults to None
                    :type version: str, optional
                    :param dateModified: date of last modification, defaults to None
                    :type dateModified: str, optional
                    :param health: client's health, defaults to None
                    :type health: str, optional
                """
                pass

    def getObjectsToInstantiate(self):
        return Client.__objectsToInstantiate

    @staticmethod
    def getSchemaName():
        return 'clientEntity'
