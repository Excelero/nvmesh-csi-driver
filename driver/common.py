import hashlib
import logging
from logging.handlers import SysLogHandler

import grpc
import sys
import os

from subprocess import Popen, PIPE

class Consts(object):
	DEFAULT_VOLUME_SIZE = 5000000000 #5GB
	PLUGIN_NAME = "nvmesh-csi.excelero.com"
	PLUGIN_VERSION = "0.01"
	SPEC_VERSION = "1.1.0"
	MIN_KUBERNETES_VERSION = "1.13"

	DEFAULT_UDS_PATH = "unix:///tmp/csi.sock"
	SYSLOG_PATH = "/dev/log"

	class VolumeAccessType(object):
		BLOCK = 'block'
		MOUNT = 'mount'

class ServerLoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger):
		self.logger = logger

	def intercept_service(self, continuation, handler_call_details):
		# gRPC Python doesn't have a complete server interceptor implementation that allow you to access the request obj
		# but we can print the method's name
		method = handler_call_details.method.split('/')[-1:][0]
		self.logger.debug('called method {}'.format(method))
		return continuation(handler_call_details)

class DriverLogger(logging.Logger):

	def __init__(self, name="NVMeshCSIDriver", level=logging.DEBUG):
		logging.Logger.__init__(self, name)
		self.log_level = level
		self.setLevel(level)
		self.add_stdout_handler()

	@staticmethod
	def _get_default_formatter():
		formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
		return formatter

	def _add_handler(self, handler):
		handler.setLevel(self.log_level)
		formatter = DriverLogger._get_default_formatter()
		handler.setFormatter(formatter)
		self.addHandler(handler)

	def add_stdout_handler(self):
		handler = logging.StreamHandler(sys.stdout)
		self._add_handler(handler)
		return handler

	def add_syslog_handler(self):
		handler = SysLogHandler(address=Consts.SYSLOG_PATH)
		self._add_handler(handler)
		return handler

def CatchServerErrors(func):
	def func_wrapper(self, request, context):
		try:
			return func(self, request, context)
		except DriverError as drvErr:
			# context.set_code(drvErr.code)
			# context.set_details(str(drvErr.message))
			context.abort(drvErr.code, str(drvErr.message))

		except Exception as ex:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			exc_tb = exc_tb.tb_next
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

			# context.set_code(grpc.StatusCode.INTERNAL)
			# context.set_details()
			details = "{type}: {msg} in {fname} on line: {lineno}".format(type=exc_type, msg=str(ex), fname=fname, lineno=exc_tb.tb_lineno)
			context.abort(grpc.StatusCode.INTERNAL, details)

	return func_wrapper

class DriverError(Exception):
	def __init__(self, code, message):
		Exception.__init__(self, message)
		self.code = code

class Utils(object):
	logger = DriverLogger("Utils")

	@staticmethod
	def volume_id_to_nvmesh_name(co_vol_name):
		# Nvmesh vol name / id cannot be longer than 23 characters
		return 'csi-' + co_vol_name[4:22]

	@staticmethod
	def is_nvmesh_volume_attached(nvmesh_volume_name):
		cmd = 'ls /dev/nvmesh/{}'.format(nvmesh_volume_name)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return exit_code == 0

	@staticmethod
	def run_command(cmd):
		Utils.logger.debug("running: {}".format(cmd))
		p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
		stdout, stderr = p.communicate()
		exit_code = p.returncode
		Utils.logger.debug("cmd: {} return exit_code={} stdout={} stderr={}".format(cmd, exit_code, stdout, stderr))
		return exit_code, stdout, stderr

	@staticmethod
	def validate_params_exists(request, attribute_list):
		for attribute_name in attribute_list:
			Utils.validate_param_exists(request, attribute_name)

	@staticmethod
	def validate_param_exists(request, attribute_name, error_msg=None):
		if not getattr(request, attribute_name):
			if not error_msg:
				error_msg = '{} was not provided'.format(attribute_name)
			raise DriverError(grpc.StatusCode.INVALID_ARGUMENT, error_msg)

	@staticmethod
	def get_nvmesh_block_device_path(nvmesh_volume_name):
		return '/dev/nvmesh/{}'.format(nvmesh_volume_name)