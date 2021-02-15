#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class GeneralSettings(Entity):
    ID = AttributeRepresentation(display='ID', dbKey='_id')
    ClusterName = AttributeRepresentation(display='Cluster Name', dbKey='clusterName')
    MaxJsonSize = AttributeRepresentation(display='Max JSON Size', dbKey='MAX_JSON_SIZE')
    ReservedBlocks = AttributeRepresentation(display='Reserved Blocks', dbKey='RESERVED_BLOCKS')
    AutoLogOutThreshold = AttributeRepresentation(display='Auto Log Out Threshold', dbKey='autoLogOutThreshold')
    CacheUpdateInterval = AttributeRepresentation(display='Cache Update Interval', dbKey='cacheUpdateInterval')
    CompatibilityMode = AttributeRepresentation(display='Compatibility Mode', dbKey='compatibilityMode')
    DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
    DaysBeforeLogEntryExpires = AttributeRepresentation(display='Days Before Log Entry Expires', dbKey='daysBeforeLogEntryExpires')
    DebugComponents = AttributeRepresentation(display='Debug Components', dbKey='debugComponents')
    Domain = AttributeRepresentation(display='Domain', dbKey='domain')
    EnableDistributedRAID = AttributeRepresentation(display='Enable Distributed RAID', dbKey='enableDistributedRAID')
    EnableLegacyFormatting = AttributeRepresentation(display='Enable Legacy Formatting', dbKey='enableLegacyFormatting')
    EnableZones = AttributeRepresentation(display='Enable Zones', dbKey='enableZones')
    FullClientReportInterval = AttributeRepresentation(display='Full Client Report Interval', dbKey='fullClientReportInterval')
    KeepaliveGracePeriod = AttributeRepresentation(display='Keepalive Grace Period', dbKey='keepaliveGracePeriod')
    LoggingLevel = AttributeRepresentation(display='Logging Level', dbKey='loggingLevel')
    RequestStatsInterval = AttributeRepresentation(display='Request Statistics Interval', dbKey='requestStatsInterval')
    sendStatsInterval = AttributeRepresentation(display='Send Statistics Interval', dbKey='sendStatsInterval')
    StatsCollectionSettings = AttributeRepresentation(display='Statistics Collection Settings', dbKey='statsCollectionSettings')
    EnableNVMf = AttributeRepresentation(display='Enable NVMf', dbKey='enableNVMf')
    EnableMultiTenancy = AttributeRepresentation(display='Enable Multi Tenancy', dbKey='enableMultiTenancy')

    @Utils.initializer
    def __init__(self, _id=None, clusterName=None, MAX_JSON_SIZE=None, RESERVED_BLOCKS=None, autoLogOutThreshold=None,
                 cacheUpdateInterval=None, compatibilityMode=None, dateModified=None, daysBeforeLogEntryExpires=None,
                 debugComponents=None, domain=None, enableDistributedRAID=None, enableLegacyFormatting=None, enableZones=None,
                 fullClientReportInterval=None, keepaliveGracePeriod=None, loggingLevel=None, requestStatsInterval=None,
                 sendStatsInterval=None, statsCollectionSettings=None, enableNVMf=None, enableMultiTenancy=None):
        pass
