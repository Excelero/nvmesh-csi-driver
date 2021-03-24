#!/usr/bin/env python
import logging
import os


class IterableEnumMeta(type):
    def __getattr__(cls, key):
        return cls.__dict__[key]

    def __setattr__(cls, key, value):
        raise TypeError('Cannot rename const attribute {0}.{1}'.format(cls.__name__, key))

    def __getitem__(cls, key):
        return cls.__dict__[key]

    def __iter__(cls):
        for key in cls.__dict__:
            if not callable(key) and type(cls.__dict__[key]) != staticmethod and not key.startswith('_'):
                yield cls.__dict__[key]

    def values(cls):
        return list(cls)


class StaticClass(object):
    def __new__(cls):
        raise Exception('Cannot instantiate Static Class {0}'.format(cls.__name__))


class Enum(StaticClass):
    __metaclass__ = IterableEnumMeta


class EcSeparationTypes(Enum):
    FULL = 'Full Separation'
    MINIMAL = 'Minimal Separation'
    IGNORE = 'Ignore Separation'

class NVMeshVolume(Enum):
    CLIENT_VOLUMES_PATH = '/proc/nvmeibc/volumes/'
    CLIENT_VOLUMES_DEVPATH = '/dev/nvmesh/'
    NVME_TARGET_BUS_ADDRESS = '/sys/bus/pci/drivers/nvmeibs/'
    NVME_PCI_SCAN = '/sys/bus/pci/rescan'
    CLIENT_BLOCK_DEVICES = '/sys/kernel/config/nvmeibc/blockdevices'

class MessageLevel(Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'

    @staticmethod
    def getInt(level):
        mappingToLoggingValues = {
            MessageLevel.DEBUG: logging.DEBUG,
            MessageLevel.WARNING: logging.WARNING,
            MessageLevel.INFO: logging.INFO,
            MessageLevel.ERROR: logging.ERROR,
        }

        return mappingToLoggingValues[level]


class VolumeStatuses(Enum):
    PENDING = 'pending'
    ONLINE = 'online'
    OFFLINE = 'offline'
    DEGRADED = 'degraded'
    UNAVAILABLE = 'unavailable'
    QUORUM_FAILED = 'quorumFailed'


class VolumeActions(Enum):
    REBUILDING = 'rebuilding'
    MARKED_FOR_DELETION = 'markedForDeletion'
    MARKED_FOR_REBUILD = 'markedForRebuild'
    REBUILD_REQUIRED = 'rebuildRequired'
    MARKED_FOR_REBUILD_OLD = 'markedForRebuild_old'
    EXTENDING = 'extending'
    INITIALIZING = 'initializing'
    TO_BE_DELETED = 'toBeDeleted'
    NONE = 'none'


class VolumeAttachmentStatus(Enum):
    BUSY = 1
    DETACHED = 2
    DETACH_FAILED = 3
    ATTACHED = 4
    ATTACH_FAILED = 5


class BlockSize(Enum):
    SIZE_4K = '4K'
    SIZE_512 = '512'


class NICSConfig(object):
    KEEP_CURRENT_CONFIG = 'keep_current_configuration'
    AT_LEAST_ONE_INFINIBAND = 'at_least_one_Infiniband'
    ALL_INFINIBAND = 'all_Infiniband'
    AT_LEAST_ONE_ROCE = 'at_least_one_Roce'
    ALL_ROCE = 'all_Roce'


class NVMeshConfFields(Enum):
    MANAGEMENT_PROTOCOL = 'MANAGEMENT_PROTOCOL'
    MANAGEMENT_SERVERS = 'MANAGEMENT_SERVERS'
    CONFIGURED_NICS = 'CONFIGURED_NICS'
    MAX_SM_QUERY_BURST = 'MAX_SM_QUERY_BURST'
    MLX5_RDDA_ENABLED = 'MLX5_RDDA_ENABLED'
    DUMP_FTRACE_ON_OOPS = 'DUMP_FTRACE_ON_OOPS'
    AUTO_ATTACH_VOLUMES = 'AUTO_ATTACH_VOLUMES'
    TOMA_BUILD_TYPE = 'TOMA_BUILD_TYPE'
    TOMA_LOG_SIZE = 'TOMA_LOG_SIZE'
    TOMA_REDIRECT_OUTPUT_TO_FILE = 'TOMA_REDIRECT_OUTPUT_TO_FILE'
    MAX_CLIENT_RSRC = 'MAX_CLIENT_RSRC'
    MCS_LOGGING_LEVEL = 'MCS_LOGGING_LEVEL'
    AGENT_LOGGING_LEVEL = 'AGENT_LOGGING_LEVEL'
    ROCE_IPV4_ONLY = 'ROCE_IPV4_ONLY'


class ManagementLogLevel(Enum):
    VERBOSE = 'VERBOSE'
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class KillSignals(Enum):
    SIGKILL = '-9'
    SIGTERM = '-15'


class WakeupTomaOptions(Enum):
    WAKEUP_NONE = 'wakeup_none'
    WAKEUP_ONE = 'wakeup_one'
    WAKEUP_ALL = 'wakeup_all'


class DiskFormats(Enum):
    FORMAT_RAID = 'format_raid'
    FORMAT_EC = 'format_ec'
    NO_FORMAT_TYPE = 'format_none'


class DiskStatuses(Enum):
    OK = 'Ok'
    ERROR = 'Error'
    FORMAT_ERROR = 'Format_Error'
    EXCLUDED = 'Excluded'
    NOT_INITIALIZED = 'Not_Initialized'
    INGESTING = 'Ingesting'
    FROZEN = 'Frozen'
    FORMATTING = 'Formatting'
    INITIALIZING = 'Initializing'
    MISSING = 'Missing'


class FormatMetadataSize(Enum):
    EC_SIZE = 8
    RAID_SIZE = 0


class DiskVendors(Enum):
    HGST = 0x1c58
    Samsung = 0x144d
    Intel = 0x8086
    Micron = 0x1344


class SimulatorStatus(Enum):
    PASSED = 0
    GENERAL_ERROR = 1
    ILLEGAL_TEST_NAME = 2
    FAILING_TESTS = 3


class SimulatorTestStatus(Enum):
    PASSED = 0
    FAILED = 1


class SocketPathes:
    SOCKET_FILE_PATH = '/var/run/NVMesh/json_uds'


class ConnectPortStatus(Enum):
    UNRESOLVED = 'UNRESOLVED'
    FAILED = 'FAILED'  # at least one interface failed
    SUCCESS = 'SUCCESS'
    SKIPPED = 'SKIPPED'


class NetworkPortAction(Enum):
    CONNECT = ['Connection', 'connect']
    DISCONNECT = ['Disconnection', 'disconnect']


class NVMeshNodeType(Enum):
    CLIENT = 'clients'
    TARGET = 'servers'


class MongoDefaults(Enum):
    PORT = '27017'
    CONF_FILE = '/etc/mongod.conf'
    SERVICE_NAME = 'mongod'
    PID_FILE = '/var/run/mongodb/mongod.pid'
    LOCK_FILE = '/tmp/mongodb-{}.sock'


class TargetStatuses(Enum):
    OK = 'Ok'


class TargetHealth(Enum):
    HEALTHY = 'healthy'
    CRITICAL = 'critical'
    ALARM = 'alarm'


class CompilatorDefaults(Enum):
    BUILD_SCRIPT_NAME = 'build_client_server_rpms.py'
    COMPILE_SCRIPT_NAME = 'compile_for_kernel_and_ofed.sh'
    BLOCK_SIZE_OPTIONS = ['512B', '4k']


class EndpointRoutes(Enum):
    CLIENTS = 'clients'
    SERVERS = 'servers'
    SERVER_CLASSES = 'serverClasses'
    DISK_CLASSES = 'diskClasses'
    DISKS = 'disks'
    LOGS = 'logs'
    USERS = 'users'
    VOLUMES = 'volumes'
    VPGS = 'volumeProvisioningGroups'
    CONFIGURATION_PROFILE = 'configurationProfiles'
    GENERAL_SETTINGS = 'generalSettings'
    LOGIN = 'login'
    MONGO_DB = 'mongoDB'
    KEYS = 'keys'
    VolumeSecurityGroups = 'volumeSecurityGroups'
    INDEX = '/'


class CLI:
    ITERATOR_THRESHOLD = 50
    RESULTS_ITERATOR_CONT = 'it'
    RESULTS_ITERATOR_QUIT = 'q'
    NVMESH_CLI_FILES_DIR = '~/.nvmesh_cli_files'
    API_SECRETS_FILE = '{}/nvmesh_api_secrets'.format(NVMESH_CLI_FILES_DIR)
    SSH_SECRETS_FILE = '{}/nvmesh_ssh_secrets'.format(NVMESH_CLI_FILES_DIR)
    HISTORY_FILE = '{}/nvmesh_cli_history'.format(NVMESH_CLI_FILES_DIR)
    DEFAULT_TIMEOUT = 60
    PERCENT_FROM_TIMEOUT_TO_VOLUME_POST_REQUEST = 0.8
    ERROR_CODE = 100
    CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class ControlJobs(Enum):
    SHUTDOWN_ALL = 'shutdownAll'
    ATTACH = 'toBeAttached'
    DETACH = 'toBeDetached'


class RAIDLevels(Enum):
    CONCATENATED = 'Concatenated'
    JBOD = 'LVM/JBOD'
    STRIPED_RAID_0 = 'Striped RAID-0'
    MIRRORED_RAID_1 = 'Mirrored RAID-1'
    STRIPED_AND_MIRRORED_RAID_10 = 'Striped & Mirrored RAID-10'
    ERASURE_CODING = 'Erasure Coding'


class VolumeDefaults(Enum):
    STRIPE_SIZE = 32
    NUMBER_OF_MIRRORS = 1
    EC_STRIPE_WIDTH = 1


class ScriptPaths(Enum):
    ATTACH_VOLUMES = '/usr/bin/nvmesh_attach_volumes'
    DETACH_VOLUMES = '/usr/bin/nvmesh_detach_volumes'
    NVMESH_TARGET = '/usr/bin/nvmesh_target'
    NVMESH_CLIENT_INSTANCE_DO = '/usr/bin/nvmesh_client_instance_do'
    NVMESH_CLI_PATH = "/usr/bin/nvmesh"

class ControlJobsScriptCmds(Enum):
    ATTACH_VOLUMES = 'nvmesh_attach_volumes'
    DETACH_VOLUMES = 'nvmesh_detach_volumes'


class ReservationModes(Enum):
    NONE = 0
    SHARED_READ_ONLY = 1
    SHARED_READ_WRITE = 2
    EXCLUSIVE_READ_WRITE = 3
    INT_TO_MODE = {
        0: 'NONE',
        1: 'SHARED_READ_ONLY',
        2: 'SHARED_READ_WRITE',
        3: 'EXCLUSIVE_READ_WRITE'
    }


class AccessLevels(Enum):
    EXCLUSIVE_READ_WRITE = 'EXCLUSIVE_READ_WRITE'
    SHARED_READ_ONLY = 'SHARED_READ_ONLY'
    SHARED_READ_WRITE = 'SHARED_READ_WRITE'
