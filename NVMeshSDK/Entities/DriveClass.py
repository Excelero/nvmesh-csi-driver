#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.Drive import Drive
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class DriveClass(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Description
            * Drives
            * DateModified
            * ModifiedBy
            * Domains
    """
    Id = AttributeRepresentation(display='Name', dbKey='_id')
    Description = AttributeRepresentation(display='Description', dbKey='description')
    Drives = AttributeRepresentation(display='Drives', dbKey='disks', type=Drive)
    DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
    ModifiedBy = AttributeRepresentation(display='Modified By', dbKey='modifiedBy')
    Domains = AttributeRepresentation(display='Domains', dbKey='domains')
    __objectsToInstantiate = ['Drives']

    @Utils.initializer
    def __init__(self, _id, disks, description=None, tags=None, modifiedBy=None, createdBy=None, dateModified=None, dateCreated=None, domains=None):
        """**Initializes drive class entity**

        :param _id: the id of the drive class
        :type _id: str
        :param disks: list of disks
        :type disks: list
        :param description: description of the drive class, defaults to None
        :type description: str, optional
        :param domains: list of awareness domains of the drive class, defaults to None
        :type domains: list, optional
        :param modifiedBy: the last user that modified the drive class, defaults to None
        :type modifiedBy: str, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        """
        pass

    def getObjectsToInstantiate(self):
        return DriveClass.__objectsToInstantiate

    @staticmethod
    def getSchemaName():
        return 'driveClassEntity'