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
			if not callable(key) and type(cls.__dict__[key])!=staticmethod and not key.startswith('_'):
				yield cls.__dict__[key]

	def values(cls):
		return list(cls)

class StaticClass(object):
	def __new__(cls):
		raise Exception('Cannot instantiate Static Class {0}'.format(cls.__name__))

class Enum(StaticClass):
	__metaclass__ = IterableEnumMeta


BASE                  = '/opt/infraClient'
LOCAL_TEST_DIR        = '/opt/infraClient'

DEFAULT_SSH_USER      = 'orchestrator'
EXCELERO_REPOS_URL    = 'https://excelero:excelero1234@repo.excelero.com/repos/{}/redhat/{}/'
SYSLOG_PATH           = '/dev/log'
TEST_REPOSITORY_DIR   = '{}/testRepository/Tests'.format(BASE)
SIMULATOR_DIR         = '{}/Simulators/'.format(BASE)
COMMON_DIR            = '{}/common'.format(BASE)
LOCAL_UTILS_DIR       = '{}/utils'.format(LOCAL_TEST_DIR)
TEST_UTILS_SCRIPTS    = '{}/utils/scripts/'.format(BASE)
TEST_UTILS_NETWORK    = '{}/utils/network/'.format(BASE)
TEST_UTILS_CONF       = '{}/utils/configurations/'.format(BASE)
EXECUTION_DIR_TEMPLATE = '/var/opt/infraClient/executions/{0}/'
NVMESH_SRC            = '/tmp/infraClient/nvmesh'
BLOCK_UNITEST_DIR     = NVMESH_SRC + '/clnt/block/unitest/'
PERF_TEST_UNITEST_DIR = NVMESH_SRC + '/perfTest/io_stress'
UNSAFE_DETACH         = '/sys/module/nvmeibc/parameters/allow_unsafe_detach'
BTEST_PATH            = '/bin/infraClient/utils/btestEX'
FIO_PATH              = '/bin/infraClient/utils/fio'
CMP_BLOCKS_PATH       = '/bin/infraClient/utils/cmp_blocks'
REPORTER_SOCKET_PATH  = '/var/opt/infraClient/reporter.sock'
KILL_TOMA_JSON_FILE   = 'killTomaDB.json'

OLD_NVMESH_FORMAT_PATH    = '/usr/bin/nvmesh_format.py'
NVMESH_FORMAT_PATH    = '/opt/NVMesh/target-repo/scripts/nvmesh_format.py'
NVMESH_SERVICE_NEW_PATH = '/opt/NVMesh/target-repo/services'
NVMESH_SERVICE_OLD_PATH = '/etc/init.d'
TOMA_LEADER_NAME_OLD_PATH = '/var/log/NVMesh/toma_leader_name'
TOMA_LEADER_NAME_NEW_PATH = '/proc/nvmeibs/toma_status/leader'

DEFAULT_IPMI_USER     = 'ADMIN'
DEFAULT_IPMI_PASS     = 'ADMIN'

SERVICE_INIT_PATH     = '/etc/init.d/'

class TestStatuses(Enum):
	NOT_STARTED        = 'NOT_STARTED'
	STARTED            = 'STARTED'
	RUNNING            = 'RUNNING'
	WARNING            = 'WARNING'
	PASSED             = 'PASSED'
	FAILED             = 'FAILED'
	TIMEOUT            = 'TIMEOUT'
	ABORTED            = 'ABORTED'
	FATAL              = 'FATAL'
	_FINISHED_STATUSES = [PASSED, FAILED, TIMEOUT, ABORTED, FATAL]

	@staticmethod
	def finishedStatuses():
		return TestStatuses._FINISHED_STATUSES

class ConfigStatuses(Enum):
	READY                     = 'READY'
	CONFIGURATION_IN_PROGRESS = 'CONFIGURATION_IN_PROGRESS'
	CONFIGURATION_FAILED      = 'CONFIGURATION_FAILED'
	POST_MORTEM               = 'POST_MORTEM'

class ContentType(Enum):
	JSON        = 'application/json'
	TAR_ARCHIVE = 'application/x-tar'
	HTML        = 'text/html'

class ComponentStatus(Enum):
	UNKNOWN       = 'UNKNOWN'
	NOT_INSTALLED = 'NOT_INSTALLED'
	IS_UP         = 'IS_UP'
	IS_DOWN       = 'IS_DOWN'

class ControlJobs(Enum):
	TO_BE_ATTACHED = 'toBeAttached'
	TO_BE_DETACHED = 'toBeDetached'

class RAIDLevels(Enum):
	LVM_JBOD        = 'LVM/JBOD'
	RAID0           = 'Striped RAID-0'
	RAID1           = 'Mirrored RAID-1'
	RAID10          = 'Striped & Mirrored RAID-10'
	ERASURE_CODING  = 'Erasure Coding'
	CONCATENATED    = 'Concatenated'

class EcSeparationTypes(Enum):
	FULL    = 'Full Separation'
	MINIMAL = 'Minimal Separation'
	IGNORE  = 'Ignore Separation'

class MkfsTypes(Enum):
	EXT3  = 'ext3'
	EXT4  = 'ext4'
	XFS   = 'xfs'
	BTRFS = 'btrfs'

class NVMeshService(Enum):
	NVMESH_TARGET              = 'nvmeshtarget'
	NVMESH_TARGET_TOMA_RESTART = 'restart-toma'
	TARGET_KERNEL_MODULE       = 'nvmeibs'
	NVMESH_CLIENT              = 'nvmeshclient'
	CLIENT_KERNEL_MODULE       = 'nvmeibc'
	NVMESH_MANAGEMENT          = 'nvmeshmgr'
	INFRA_CLIENT               = 'infraclient'

class NVMeshPackageName(Enum):
	TARGET = 		'NVMesh-target'
	CLIENT = 		'NVMesh-client'
	CORE = 			'nvmesh-core'
	MANAGEMENT = 	'nvmesh-management'
	# this is to support current branches before the RPM rename - after a small integration phase, it should be removed
	MANAGEMENT_OLD = 	'NVMesh-management'


class NVMeshServiceInitPath(Enum):
	NVMESH_TARGET_FILE = os.path.join(SERVICE_INIT_PATH, NVMeshService.NVMESH_TARGET)
	NVMESH_CLIENT_FILE = os.path.join(SERVICE_INIT_PATH, NVMeshService.NVMESH_CLIENT)
	NVMESH_MGMT_FILE   = os.path.join(SERVICE_INIT_PATH, NVMeshService.NVMESH_MANAGEMENT)

class NVMeshPid(Enum):
	TOMA_PID_PATH             = '/var/run/NVMesh/nvmeshtarget/toma.pid'
	MANAGEMENT_CM_PID_PATH    = '/var/run/NVMesh/managementCM.pid'
	OLD_MANAGEMENT_AGENT_PID_PATH = '/var/run/NVMesh/nvmeshclient/managementAgent.pid'
	MANAGEMENT_AGENT_PID_PATH = '/var/run/NVMesh/managementAgent.pid'
	MANAGEMENT_AGENT_PATH     = '/opt/NVMesh/client-repo/management_cm/managementAgent.py'
	MANAGEMENT_PID_PATH       = '/var/run/NVMesh/nvmeshmgr/management.pid'
	#Names used for ProcessManager class to work against the PIDs
	TOMA_PID_NAME             = 'nvmeibt_toma'
	MANAGEMENT_AGENT_PID_NAME = '/opt/NVMesh/.*/managementAgent.py'
	MANAGEMENT_CM_PID_NAME    = 'management_cm/managementCM.py'
	MANAGEMENT_CM_PATH        = '/opt/NVMesh/client-repo/management_cm/managementCM.py'
	MANAGEMENT_PID_NAME       = 'management/app.js'

class NVMeshVolume(Enum):
	CLIENT_VOLUMES_PATH     = '/proc/nvmeibc/volumes/'
	CLIENT_VOLUMES_DEVPATH  = '/dev/nvmesh/'
	NVME_TARGET_BUS_ADDRESS = '/sys/bus/pci/drivers/nvmeibs/'
	NVME_PCI_SCAN           = '/sys/bus/pci/rescan'
	CLIENT_BLOCK_DEVICES    = '/sys/kernel/config/nvmeibc/blockdevices'

class TomaProc(Enum):
	TOMA_STATUS_ALL  = '/proc/nvmeibs/toma_status/all'
	TOMA_STATUS_BDEV = '/proc/nvmeibs/toma_status/bdev'
	TOMA_STATUS_CFG  = '/proc/nvmeibs/toma_status/cfg'
	TOMA_STATUS_DISK = '/proc/nvmeibs/toma_status/disk'
	TOMA_STATUS_DSEG = '/proc/nvmeibs/toma_status/dseg'
	TOMA_STATUS_IB   = '/proc/nvmeibs/toma_status/ib'
	TOMA_STATUS_RAFT = '/proc/nvmeibs/toma_status/raft'
	TOMA_STATUS_RTM  = '/proc/nvmeibs/toma_status/rtm '
	TOMA_STATUS_TOPO = '/proc/nvmeibs/toma_status/topo'

class MonitoredServices(Enum):
	TOMA              = 'tomaStatus'
	MANAGEMENT_AGENT  = 'managementAgentStatus'
	MANAGEMENT        = 'managementStatus'
	HOST_KEEP_ALIVE   = 'serverKeepAlive'
	MCS               = 'mcsStatus'

class IOEngines(Enum):
	LIBAIO   = 'libaio'
	SYNC     = 'sync'
	POSIXAIO = 'posixaio'
	MMAP     = 'mmap'

class FIOpattern(Enum):
	READ      = 'read'
	WRITE     = 'write'
	TRIM      = 'trim'
	RANDREAD  = 'randread'
	RANDWRITE = 'randwrite'
	RANDRW    = 'randrw'
	TRIMWRITE = 'trimwrite'


class MessageLevel(Enum):
	DEBUG 	= 'DEBUG'
	INFO 	= 'INFO'
	WARNING = 'WARNING'
	ERROR 	= 'ERROR'

	@staticmethod
	def getInt(level):
		mappingToLoggingValues = {
			MessageLevel.DEBUG: 	logging.DEBUG,
			MessageLevel.WARNING: 	logging.WARNING,
			MessageLevel.INFO: 		logging.INFO,
			MessageLevel.ERROR: 	logging.ERROR,
		}

		return mappingToLoggingValues[level]

class SwitchHandler(Enum):
	SW_ETHERNET            = 'eth'
	SW_ETHERNET_FULLNAME   = 'ethernet'
	SW_INFINIBAND          = 'ib'
	SW_VPI                 = 'vpi'
	SW_INFINIBAND_FULLNAME = 'infiniband'
	INTERFACE_UP           = 'up'
	INTERFACE_DOWN         = 'down'
	FLOWCONTROL_ON         = 'on'
	FLOWCONTROL_OFF        = 'off'
	HCA_INFINIBAND         = 'InfiniBand'
	HCA_ETHERNET           = 'Ethernet'
	INTERFACE_CX3          = 'cx3'
	INTERFACE_CX4          = 'cx4'
	VLAN_ACCESS            = 'access'
	VLAN_ACCESS_DCB        = 'access-dcb'
	VLAN_HYBRID            = 'hybrid'
	VLAN_TRUNK             = 'trunk'
	UNMANAGED_SW           = 'unmanaged'

class SwitchVendor(Enum):
	DELL           = 'dell'
	MLNX           = 'mellanox'
	UNMANAGED_MLNX = 'unmanaged_mlnx'
	CUMULUS        = 'cumulus'
	CISCO          = 'cisco'

class FiberType(Enum):
	INFINIBAND = SwitchHandler.HCA_INFINIBAND
	ROCE       = SwitchHandler.HCA_ETHERNET

class NVMeshDebugLevel(Enum):
	RELEASE = 'Release'
	DELEASE = 'Delease'
	DEBUG 	= 'Debug'

class NVMeshModuleDebugLevel(Enum):
	NVMEIBC_DBG_LEVEL       = '/sys/module/nvmeibc/parameters/debug_level'
	NVMEIBS_DBG_LEVEL       = '/sys/module/nvmeibs/parameters/debug_level'
	NVMEIB_COMMON_DBG_LEVEL = '/sys/module/nvmeib_common/parameters/debug_level'
	DEBUG_LEVEL_OFF         = 1
	DEBUG_LEVEL_ON          = 2

class BlockUniTestCommand(Enum):
	CLEAN   = 'clean'
	BUILD   = 'build'
	REBUILD = 'rebuild'
	RUN     = 'run'
	EXEC    = 'exec'
	CI      = 'ci'
	DEPEND  = 'depend'

class TestType(Enum):
	TEST         = 'Test'
	DISASTER     = 'Disaster'
	CONTROL_FLOW = 'ControlFlow'

class OsDistName(Enum):
	CENTOS_OS = 'centos'
	REDHAT_OS = 'redhat'
	UBUNTU_OS = 'ubuntu'
	SUSE_OS   = 'suse'
	MINT_OS   = 'linuxmint'
	FEDORA_OS = 'fedora'

class OsDistInstaller(Enum):
	FEDORA_PKG_INSTALLER = 'dnf'
	REDHAT_PKG_INSTALLER  = 'yum'
	UBUNTU_PKG_INSTALLER = 'apt'
	SUSE_PKG_INSTALLER    = 'zypper'

class OsDistPackageMgr(Enum):
	REDHAT_PKG_MGR  = 'rpm'
	UBUNTU_PKG_MGR = 'dpkg'
	SUSE_PKG_MGR    = 'rpm'

class OsDistPackageType(Enum):
	REDHAT_PKG_TYPE  = 'rpm'
	UBU8NTU_PKG_TYPE = 'deb'
	SUSE_PKG_TYPE    = 'rpm'

class NVMeshConfig(Enum):
	CONFIG_FILE = '/etc/opt/NVMesh/nvmesh.conf'

class TomaTraceConfig(Enum):
	CONFIG_FILE = '/var/log/NVMesh/trace.config'

class VolumeStatuses(Enum):
	PENDING                   = 'pending'
	ONLINE                    = 'online'
	OFFLINE                   = 'offline'
	REBUILDING                = 'rebuilding'
	DEGRADED                  = 'degraded'
	MARKED_FOR_DELETION       = 'markedForDeletion'
	MARKED_FOR_FORCE_DELETION = 'markedForForceDeletion'
	MARKED_FOR_REBUILD        = 'markedForRebuild'
	REBUILD_REQUIRED          = 'rebuildRequired'
	MARKED_FOR_REBUILD_OLD    = 'markedForRebuild_old'
	EXTENDING                 = 'extending'
	INITIALIZING              = 'initializing'
	UNAVAILABLE               = 'unavailable'
	TO_BE_DELETED             = 'toBeDeleted'
	QUORUM_FAILED             = 'quorumFailed'

class VolumeAttachmentStatus(Enum):
	BUSY 	      = 1
	DETACHED      = 2
	DETACH_FAILED = 3
	ATTACHED      = 4
	ATTACH_FAILED = 5

class BlockSize(Enum):
	SIZE_4K  = '4K'
	SIZE_512 = '512'

class NICSConfig(object):
	KEEP_CURRENT_CONFIG     = 'keep_current_configuration'
	AT_LEAST_ONE_INFINIBAND = 'at_least_one_Infiniband'
	ALL_INFINIBAND          = 'all_Infiniband'
	AT_LEAST_ONE_ROCE       = 'at_least_one_Roce'
	ALL_ROCE                = 'all_Roce'

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
	VERBOSE	= 'VERBOSE'
	DEBUG 	= 'DEBUG'
	INFO 	= 'INFO'
	WARNING = 'WARNING'
	ERROR 	= 'ERROR'

class KillSignals(Enum):
	SIGKILL = '-9'
	SIGTERM = '-15'

class WakeupTomaOptions(Enum):
	WAKEUP_NONE = 'wakeup_none'
	WAKEUP_ONE = 'wakeup_one'
	WAKEUP_ALL = 'wakeup_all'

class DiskFormats(Enum):
	FORMAT_RAID = 'format_raid'
	FORMAT_EC   = 'format_ec'
	NO_FORMAT_TYPE = 'format_none'

class DiskStatuses(Enum):
	OK              = 'Ok'
	ERROR           = 'Error'
	FORMAT_ERROR    = 'Format_Error'
	EXCLUDED        = 'Excluded'
	NOT_INITIALIZED = 'Not_Initialized'
	INGESTING       = 'Ingesting'
	FROZEN          = 'Frozen'
	FORMATTING      = 'Formatting'
	INITIALIZING    = 'Initializing'
	MISSING         = 'Missing'

class FormatMetadataSize(Enum):
	EC_SIZE   = 8
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
	FAILED = 'FAILED'		# at least one interface failed
	SUCCESS = 'SUCCESS'
	SKIPPED = 'SKIPPED'

class NetworkPortAction(Enum):
	CONNECT    = ['Connection', 'connect']
	DISCONNECT = ['Disconnection', 'disconnect']

class NVMeshNodeType(Enum):
	CLIENT = 'clients'
	TARGET = 'servers'

class MongoDefaults(Enum):
	PORT         = '27017'
	CONF_FILE    = '/etc/mongod.conf'
	SERVICE_NAME = 'mongod'
	PID_FILE     = '/var/run/mongodb/mongod.pid'
	LOCK_FILE    = '/tmp/mongodb-{}.sock'

class TargetStatuses(Enum):
	OK = 'Ok'

class TargetHealth(Enum):
	HEALTHY  = 'healthy'
	CRITICAL = 'critical'
	ALARM    = 'alarm'

class CompilatorDefaults(Enum):
	BUILD_SCRIPT_NAME = 'build_client_server_rpms.py'
	COMPILE_SCRIPT_NAME = 'compile_for_kernel_and_ofed.sh'
	BLOCK_SIZE_OPTIONS = ['512B', '4k']
