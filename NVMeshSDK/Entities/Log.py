#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class Log(Entity):
    """
    Static class attributes to use with MongoObj
            * Id
            * Timestamp
            * Level
            * Message
            * AcknowledgedBy
    """
    Id = AttributeRepresentation(display='ID', dbKey='_id')
    TimeStamp = AttributeRepresentation(display='Timestamp', dbKey='timestamp')
    Level = AttributeRepresentation(display='Level', dbKey='level')
    Message = AttributeRepresentation(display='Message', dbKey='message')
    AcknowledgedBy = AttributeRepresentation(display='Acknowledged By', dbKey='acknowledgedBy')

    @Utils.initializer
    def __init__(self, _id=None, timestamp=None, level=None, message=None, rawMessage=None, meta=None, acknowledgedBy=None, dateModified=None):
        """Initializes Log entity]

        :param _id: the id of the log, defaults to None
        :type _id: str, optional
        :param timestamp: the timestamp of the log , defaults to None
        :type timestamp: str, optional
        :param level: the level of the log, defaults to None
        :type level: str, optional
        :param message: the message of the log, defaults to None
        :type message: str, optional
        :param acknowledgedBy: the user that acknowledged the log, defaults to None
        :type acknowledgedBy: str, optional
        :param dateModified: date of last modification, defaults to None
        :type dateModified: str, optional
        """
        pass

    @staticmethod
    def getSchemaName():
        return 'logEntity'