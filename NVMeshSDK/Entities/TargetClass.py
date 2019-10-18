#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class TargetClass(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Description
            * TargetNodes
            * DateModified
            * ModifiedBy
            * Domains
    """
    Id = AttributeRepresentation(display='Name', dbKey='name')
    Description = AttributeRepresentation(display='Description', dbKey='description')
    TargetNodes = AttributeRepresentation(display='Targets', dbKey='targetNodes')
    DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
    ModifiedBy = AttributeRepresentation(display='Modified By', dbKey='modifiedBy')
    Domains = AttributeRepresentation(display='Domains', dbKey='domains')

    @Utils.initializer
    def __init__(self, name, targetNodes, _id=None, description=None, domains=None,
                 modifiedBy=None, createdBy=None, dateModified=None, dateCreated=None, servers=None, index=None):
        """**Initializes target class entity**

        :param name: target class name
        :type name: str
        :param targetNodes: list of target IDs
        :type targetNodes: list
        :param description: description of the target class, defaults to None
        :type description: str, optional
        :param domains: list of awareness domains of the target class, defaults to None
        :type domains: list, optional
        :param modifiedBy: the last user that modified the target class, defaults to None
        :type modifiedBy: str, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        """
        self._id = self.name

    @staticmethod
    def getSchemaName():
        return 'targetClassEntity'


