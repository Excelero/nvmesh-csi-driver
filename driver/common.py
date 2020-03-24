import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import SysLogHandler
from subprocess import Popen, PIPE
import grpc

from NVMeshSDK.APIs.VolumeAPI import VolumeAPI
from NVMeshSDK.Entities.Volume import Volume
from NVMeshSDK.ConnectionManager import ConnectionManager, ManagementTimeout
from config import Config
from consts import Consts


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
			self.logger.warning("Driver Error caught in gRPC call {} - Code: {} Message:{}".format(func.__name__, str(drvErr.code), str(drvErr.message)))
			context.abort(drvErr.code, str(drvErr.message))

		except Exception as ex:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			exc_tb = exc_tb.tb_next
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

			details = "{type}: {msg} in {fname} on line: {lineno}".format(type=exc_type, msg=str(ex), fname=fname, lineno=exc_tb.tb_lineno)
			self.logger.warning("Error caught in gRPC call {} - {}".format(func.__name__, details))
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

	@staticmethod
	def interruptable_sleep(duration, sleep_interval=1):
		# time.sleep doesn't interrupt on signals (for example SIGTERM when trying to terminate the container)
		# so we will make many short sleeps
		for i in range(int(duration / sleep_interval)):
			time.sleep(sleep_interval)

	@staticmethod
	def set_volume_readonly(nvmesh_volume_name):
		cmd = "echo -n '#{vol_name}|enforce_readonly 1' > /proc/nvmeibc/cli/cli".format(vol_name=nvmesh_volume_name)
		return Utils.run_command(cmd)

	@staticmethod
	def nvmesh_attach_volume(nvmesh_volume_name):
		exit_code, stdout, stderr = Utils.run_command('python /host/bin/nvmesh_attach_volumes {}'.format(nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

	@staticmethod
	def nvmesh_detach_volume(nvmesh_volume_name):
		exit_code, stdout, stderr = Utils.run_command('python /host/bin/nvmesh_detach_volumes {}'.format(nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_detach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

	@staticmethod
	def wait_for_volume_io_enabled(nvmesh_volume_name, timeout=30):
		now = datetime.now()
		max_time = datetime.now() + timedelta(seconds=timeout)
		volume_status = None

		while now <= max_time:
			volume_status = Utils.get_volume_status(nvmesh_volume_name)
			if volume_status["dbg"] == '0x200':
				# this means IO is Enabled
				return True

			Utils.logger.debug("Waiting for volume {} to have IO Enabled. current status is: 'status':'{}', 'dbg':'{}'".format(nvmesh_volume_name, volume_status["status"], volume_status["dbg"]))
			time.sleep(1)
			now = datetime.now()

		raise DriverError(grpc.StatusCode.INTERNAL, "Timed-out after waiting {} seconds for volume {} to have IO Enabled. volume status: {}".format(timeout, nvmesh_volume_name, volume_status))

	@staticmethod
	def get_volume_status(nvmesh_volume_name):
		volume_status_proc = '/proc/nvmeibc/volumes/{}/status.json'.format(nvmesh_volume_name)

		with open(volume_status_proc) as fp:
			volume_status = json.load(fp)
			return volume_status

class NVMeshSDKHelper(object):
	logger = DriverLogger("NVMeshSDKHelper")

	@staticmethod
	def _try_get_sdk_instance():
		protocol = Config.MANAGEMENT_PROTOCOL
		managementServers = Config.MANAGEMENT_SERVERS
		user = Config.MANAGEMENT_USERNAME
		password = Config.MANAGEMENT_PASSWORD

		serversWithProtocol = ['{0}://{1}'.format(protocol, server) for server in managementServers.split(',')]

		return ConnectionManager.getInstance(managementServer=serversWithProtocol, user=user, password=password, logToSysLog=False)

	@staticmethod
	def init_sdk():
		connected = False

		# try until able to connect to NVMesh Management
		while not connected:
			try:
				NVMeshSDKHelper._try_get_sdk_instance()
				connected = ConnectionManager.getInstance().isAlive()
			except ManagementTimeout as ex:
				NVMeshSDKHelper.logger.info("Waiting for NVMesh Management server on {}".format(Config.MANAGEMENT_SERVERS))
				Utils.interruptable_sleep(10)

		print("Connected to NVMesh Management server on {}".format(ConnectionManager.getInstance().managementServer))
