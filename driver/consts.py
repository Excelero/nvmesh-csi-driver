from csi.csi_pb2 import VolumeCapability

DEFAULT_VOLUME_SIZE = 5000000000
DEFAULT_DRIVER_NAME = "nvmesh-csi.excelero.com"
DEFAULT_UDS_PATH = "unix:///tmp/csi.sock"
SYSLOG_PATH = "/dev/log"
SINGLE_CLUSTER_ZONE_NAME = 'single-zone-cluster'
NODE_DRIVER_TOPOLOGY_PATH = '/topology/zones'

class FSType(object):
	XFS = 'xfs'
	EXT4 = 'ext4'

class DriverType(object):
	Controller = 'Controller'
	Node = 'Node'

class VolumeAccessType(object):
	BLOCK = 'block'
	MOUNT = 'mount'

class TopologyType(object):
	SINGLE_ZONE_CLUSTER = 'single-zone-cluster'
	MULTIPLE_NVMESH_CLUSTERS = 'multiple-nvmesh-clusters'

class TopologyKey(object):
	ZONE = DEFAULT_DRIVER_NAME + '/zone'

class ZoneSelectionPolicy(object):
	RANDOM = 'random'
	ROUND_ROBIN = 'round-robin'

class AccessMode(object):
	SINGLE_NODE_WRITER = VolumeCapability.AccessMode.SINGLE_NODE_WRITER
	MULTI_NODE_READER_ONLY = VolumeCapability.AccessMode.MULTI_NODE_READER_ONLY
	MULTI_NODE_MULTI_WRITER = VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER

	@staticmethod
	def from_nvmesh(stringValue):
		mapping_dict = {
			'EXCLUSIVE_READ_WRITE': AccessMode.SINGLE_NODE_WRITER,
			'SHARED_READ_ONLY': AccessMode.MULTI_NODE_READER_ONLY,
			'SHARED_READ_WRITE': AccessMode.MULTI_NODE_MULTI_WRITER
		}

		value = mapping_dict.get(stringValue, None)
		if not value:
			raise ValueError('Unknown NVMesh Exclusive Mode value of %s. allowed values are: %s' % (stringValue, mapping_dict.keys()))

		return value

	@staticmethod
	def to_nvmesh(integerValue):
		mapping_dict = {
			AccessMode.SINGLE_NODE_WRITER: 'EXCLUSIVE_READ_WRITE',
			AccessMode.MULTI_NODE_READER_ONLY: 'SHARED_READ_ONLY',
			AccessMode.MULTI_NODE_MULTI_WRITER: 'SHARED_READ_WRITE'
		}

		string_value = mapping_dict.get(integerValue, None)
		if not string_value:
			raise ValueError('Unknown CSI AccessMode value of %s. allowed values are: %s' % (integerValue, mapping_dict.keys()))

		return string_value

	@staticmethod
	def to_csi_string(integerValue):
		mapping_dict = {
			AccessMode.SINGLE_NODE_WRITER: 'SINGLE_NODE_WRITER',
			AccessMode.MULTI_NODE_READER_ONLY: 'MULTI_NODE_READER_ONLY',
			AccessMode.MULTI_NODE_MULTI_WRITER: 'MULTI_NODE_MULTI_WRITER'
		}

		string_value =  mapping_dict.get(int(integerValue), None)
		if not string_value:
			raise ValueError('Unknown CSI AccessMode value of %s. allowed values are: %s' % (integerValue, mapping_dict.keys()))

		return string_value

	@staticmethod
	def allowed_access_modes():
		return [
			AccessMode.SINGLE_NODE_WRITER,
			AccessMode.MULTI_NODE_READER_ONLY,
			AccessMode.MULTI_NODE_MULTI_WRITER
		]

	@staticmethod
	def fromCsiString(access_mode_string):
		mapping_dict = {
			'SINGLE_NODE_WRITER': AccessMode.SINGLE_NODE_WRITER,
			'MULTI_NODE_READER_ONLY': AccessMode.MULTI_NODE_READER_ONLY,
			'MULTI_NODE_MULTI_WRITER': AccessMode.MULTI_NODE_MULTI_WRITER
		}

		return mapping_dict.get(access_mode_string, None)



