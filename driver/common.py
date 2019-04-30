import logging
from logging.handlers import SysLogHandler

import grpc
import sys
import os


class Consts(object):
	PLUGIN_NAME = "nvmesh-csi.excelero.com"
	PLUGIN_VERSION = "0.01"
	SPEC_VERSION = "1.0.0"
	MIN_KUBERNETES_VERSION = "1.13"

	DEFAULT_UDS_PATH = "unix:///tmp/csi.sock"
	SYSLOG_PATH = "/dev/log"

class ServerLoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger):
		self.logger = logger

	def intercept_service(self, continuation, handler_call_details):
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
		formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
			context.set_code(drvErr.code)
			context.set_details(str(drvErr.message))
			return None

		except Exception as ex:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			exc_tb = exc_tb.tb_next
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

			context.set_code(grpc.StatusCode.INTERNAL)
			context.set_details("{type}: {msg} in {fname} on line: {lineno}".format(type=exc_type, msg=str(ex), fname=fname, lineno=exc_tb.tb_lineno))
			return None

	return func_wrapper

class DriverError(Exception):
	def __init__(self, code, message):
		Exception.__init__(self, message)
		self.code = code
