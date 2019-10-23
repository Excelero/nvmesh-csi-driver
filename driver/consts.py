from csi.csi_pb2 import VolumeCapability


def read_value_from_file(filename):
	with open(filename) as file:
		return file.readline()


class Consts(object):
	DEFAULT_VOLUME_SIZE = 5000000000 #5GB
	DRIVER_NAME = "nvmesh-csi.excelero.com"
	DRIVER_VERSION = read_value_from_file("/version")
	SPEC_VERSION = "1.1.0"

	DEFAULT_UDS_PATH = "unix:///tmp/csi.sock"
	SYSLOG_PATH = "/dev/log"

	ALLOWED_ACCESS_MODES = [
		'MULTI_NODE_MULTI_WRITER',
		'MULTI_NODE_READER_ONLY'
	]

	class DriverType(object):
		Controller = 'Controller'
		Node = 'Node'

	class VolumeAccessType(object):
		BLOCK = 'block'
		MOUNT = 'mount'
