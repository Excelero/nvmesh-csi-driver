#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Key(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * UUID
            * DateModified
            * DateCreated
            * ModifiedBy
            * CreatedBy
            * Description
    """
    Id = AttributeRepresentation(display='Name', dbKey='_id')
    UUID = AttributeRepresentation(display='UUID', dbKey='uuid')
    DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
    DateCreated = AttributeRepresentation(display='Date Created', dbKey='dateCreated')
    ModifiedBy = AttributeRepresentation(display='Modified By', dbKey='modifiedBy')
    CreatedBy = AttributeRepresentation(display='Created By', dbKey='createdBy')
    Description = AttributeRepresentation(display='Description', dbKey='description')
    DBUUID = AttributeRepresentation(display='DB UUID', dbKey='dbUUID')

    @Utils.initializer
    def __init__(self, _id=None, uuid=None, dateModified=None, dateCreated=None, modifiedBy=None, createdBy=None, description=None, dbUUID=None):
        """Initializes Key entity

        :param _id: the id of the key, defaults to None
        :type _id: str, optional
        :param uuid: the uuid of the key , defaults to None
        :type uuid: str, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        :param dateCreated: date of creation, defaults to None
        :type dateCreated: str, optional
        :param modifiedBy: the last user that modified the key, defaults to None
        :type modifiedBy: str, optional
        :param createdBy: the user that created the key, defaults to None
        :type createdBy: str, optional
        :param description: the description of the key, defaults to None
        :type description: str, optional
        """
        pass