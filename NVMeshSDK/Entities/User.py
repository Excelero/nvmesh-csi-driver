#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class User(Entity):
    """
    Static class attributes to use with MongoObj
            * Email
            * Role
            * DateModified
            * ModifiedBy
            * NotificationLevel
    """
    Email = AttributeRepresentation(display='Email', dbKey='email')
    Id = Email
    Role = AttributeRepresentation(display='Role', dbKey='role')
    DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
    ModifiedBy = AttributeRepresentation(display='Modified By', dbKey='modifiedBy')
    NotificationLevel = AttributeRepresentation(display='Notification Level', dbKey='notificationLevel')

    @Utils.initializer
    def __init__(self, email, role, notificationLevel, password=None,_id=None, layout=None, relogin=False, modifiedBy=None, createdBy=None,
                 eulaDateOfSignature=None, eulaSignature=None, hasAcceptedEula=None, dateModified=None, dateCreated=None):
        """**Initializes user entity**

        :param email: user's email
        :type email: str
        :param role: role of the user, Options: Observer, Admin.
        :type role: str
        :param notificationLevel: notificationLevel of the user possible values are: NONE, WARNING & ERROR.
        :type notificationLevel: str
        :param password: the password of the user.
        :type password: str
        :param confirmationPassword: the confirmation password of the user.
        :type confirmationPassword: str
        :param relogin: determines if the newly created user will be prompted to change the password upon first login, defaults to None
        :type relogin: bool, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        """
        self._id = email
        if hasattr(self, 'password'):
            self.confirmationPassword = self.password

    @staticmethod
    def getSchemaName():
        return 'userEntity'