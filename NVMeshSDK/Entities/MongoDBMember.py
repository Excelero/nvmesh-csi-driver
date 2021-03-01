#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class MongoDBMember(Entity):
    """
    Static class attributes.
            * Name
            * Host
            * Port
            * State
            * DatabaseSize
            * FreeSpace
            * LastHeartbeat
            * LastHeartbeatReceived
            * LastHeartbeatMessage
            * Health
    """
    Name = AttributeRepresentation(display='Name', dbKey='name')
    Host = AttributeRepresentation(display='Host', dbKey='host')
    Port = AttributeRepresentation(display='Port', dbKey='port')
    State = AttributeRepresentation(display='State', dbKey='state')
    DatabaseSize = AttributeRepresentation(display='Database Size', dbKey='dbSize')
    FreeSpace = AttributeRepresentation(display='Free Space', dbKey='freeSpace')
    LastHeartbeat = AttributeRepresentation(display='Last Heartbeat', dbKey='lastHeartbeat')
    LastHeartbeatReceived = AttributeRepresentation(display='Last Heartbeat Received', dbKey='lastHeartbeatRecv')
    LastHeartbeatMessage = AttributeRepresentation(display='Last Heartbeat Message', dbKey='lastHeartbeatMessage')
    Health = AttributeRepresentation(display='Health', dbKey='health')

    @Utils.initializer
    def __init__(self, name=None, host=None, port=None, state=None, dbSize=None, freeSpace=None, lastHeartbeat=None,
                 lastHeartbeatRecv=None, lastHeartbeatMessage=None, health=None):
        """**Initializes MongoDB member entity**

        :param name: member's name, defaults to None
        :type name: str, optional
        :param host: member's host, defaults to None
        :type host: str, optional
        :param port: member's port, defaults to None
        :type port: int, optional
        :param state: member's state, defaults to None
        :type state: int, optional
        :param dbSize: member's DB size in bytes, defaults to None
        :type dbSize: int, optional
        :param freeSpace: DB free space in bytes, defaults to None
        :type freeSpace: int, optional
        :param lastHeartbeat: reflects the last time the PRIMARY received a response from a heartbeat that it sent to this member, defaults to None
        :type lastHeartbeat: str, optional
        :param lastHeartbeatRecv: reflects the last time the PRIMARY received a heartbeat request from this member, defaults to None
        :type lastHeartbeatRecv: str, optional
        :param lastHeartbeatMessage: last heartbeat message, defaults to None
        :type lastHeartbeatMessage: str, optional
        :param health: member's health, defaults to None
        :type health: int, optional
        """

        pass
