import os

from csi.csi_pb2 import VolumeCapability


def read_value_from_file(filename):
	with open(filename) as file:
		return file.readline()

def read_bash_file(filename):
	g = {}
	l = {}

	if os.path.exists(filename):
		execfile(filename, g, l)

	return l

DEFAULT_VOLUME_SIZE = 5000000000 #5GB
DRIVER_NAME = "nvmesh-csi.excelero.com"
DRIVER_VERSION = read_value_from_file("/version")
SPEC_VERSION = "1.1.0"
NVMESH_VERSION_INFO = read_bash_file('/opt/NVMesh/client-repo/version')

DEFAULT_UDS_PATH = "unix:///tmp/csi.sock"
SYSLOG_PATH = "/dev/log"

class DriverType(object):
	Controller = 'Controller'
	Node = 'Node'

class VolumeAccessType(object):
	BLOCK = 'block'
	MOUNT = 'mount'

class AccessMode(object):
	SINGLE_NODE_WRITER = VolumeCapability.AccessMode.SINGLE_NODE_WRITER
	MULTI_NODE_READER_ONLY = VolumeCapability.AccessMode.MULTI_NODE_READER_ONLY
	MULTI_NODE_MULTI_WRITER = VolumeCapability.AccessMode.MULTI_NODE_MULTI_WRITER

	@staticmethod
	def from_nvmesh(stringValue):
		mapping_dict = {
			'EXCLUSIVE_RW': AccessMode.SINGLE_NODE_WRITER,
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
			AccessMode.SINGLE_NODE_WRITER: 'EXCLUSIVE_RW',
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
