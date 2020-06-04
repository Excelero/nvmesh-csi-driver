import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from logging.handlers import SysLogHandler
from subprocess import Popen, PIPE
import grpc

from NVMeshSDK.ConnectionManager import ConnectionManager, ManagementTimeout
from config import Config
import consts as Consts


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
			self.logger.exception("Driver Error with stack trace")
			context.abort(drvErr.code, str(drvErr.message))

		except Exception as ex:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			exc_tb = exc_tb.tb_next
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]

			if Config.PrintTraceBacks:
				import traceback
				tb = traceback.format_exc()
				print(tb)

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
		# NVMesh volume name / id cannot be longer than 23 characters
		return 'csi-' + co_vol_name[4:22]

	@staticmethod
	def is_nvmesh_volume_attached(nvmesh_volume_name):
		cmd = 'ls /dev/nvmesh/{}'.format(nvmesh_volume_name)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return exit_code == 0

	@staticmethod
	def run_command(cmd, debug=True):
		if debug:
			Utils.logger.debug("running: {}".format(cmd))
		p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
		stdout, stderr = p.communicate()
		exit_code = p.returncode
		if debug:
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

	# legacy API of calling nvmesh_attach_volumes before Exclusive Access feature introduced
	@staticmethod
	def _attach_volume_legacy(nvmesh_volume_name):
		exit_code, stdout, stderr = Utils.run_command('python /host/bin/nvmesh_attach_volumes --wait_for_attach {}'.format(nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

	@staticmethod
	def _attach_volume_with_access_mode(nvmesh_volume_name, nvmesh_access_mode):
		cmd_template = 'python /host/bin/nvmesh_attach_volumes --wait_for_attach --json --access {access} {volume}'
		cmd = cmd_template.format(access=nvmesh_access_mode, volume=nvmesh_volume_name)
		exit_code, stdout, stderr = Utils.run_command(cmd)

		try:
			results = json.loads(stdout)
		except Exception as ex:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

		if results.get('status') == 'failed':
			# General Script Failure
			raise DriverError(grpc.StatusCode.INTERNAL,
							  "nvmesh_attach_volumes failed: error_code: {} error: {} cmd: {}".format(results['error_code'], results['error'], cmd))
		else:
			volumes_results = results.get('volumes', [])
			if nvmesh_volume_name in volumes_results:
				# volumes_results is an object with volume_name as keys. we only need to handle one volume
				volume_res = volumes_results[nvmesh_volume_name]
				volume_status = volume_res['status']
				if volume_status in ['Attached IO Enabled', 'Attached']:
					# Success
					Utils.logger.debug('Volume {} attached with reservation mode {}'.format(nvmesh_volume_name, nvmesh_access_mode))
				elif volume_status == 'Already Attached':
					if 'error' in volume_res:
						raise DriverError(grpc.StatusCode.FAILED_PRECONDITION,
									  "nvmesh_attach_volumes failed: {} error: {} cmd: {}".format(volume_status, volume_res.get('error', None), cmd))
					else:
						Utils.logger.debug('Volume {} is already attached with the requested access mode. output: {}'.format(nvmesh_volume_name, stdout))
				elif volume_status == 'Reservation Mode Denied':
					raise DriverError(grpc.StatusCode.FAILED_PRECONDITION,
									  "nvmesh_attach_volumes failed: {} error: {} cmd: {}".format(volume_status, volume_res.get('error', None), cmd))
				else:
					raise DriverError(grpc.StatusCode.INTERNAL,
									  "nvmesh_attach_volumes failed: {} error: {} cmd: {}".format(volume_status, volume_res.get('error', None), cmd))

	@staticmethod
	def nvmesh_attach_volume(nvmesh_volume_name, requested_nvmesh_access_mode):
		if FeatureSupport.AccessMode:
			Utils.check_if_access_mode_allowed(requested_nvmesh_access_mode, nvmesh_volume_name)
			Utils.logger.debug('using nvmesh_attach_volume with --access and --json')
			Utils._attach_volume_with_access_mode(nvmesh_volume_name, requested_nvmesh_access_mode)
		else:
			# Backward Compatibility for NVMesh versions without exclusive access feature
			Utils.logger.debug('using legacy nvmesh_attach_volume without --access or --json')
			Utils._attach_volume_legacy(nvmesh_volume_name)

	@staticmethod
	def nvmesh_detach_volume(nvmesh_volume_name):
		exit_code, stdout, stderr = Utils.run_command('python /host/bin/nvmesh_detach_volumes {}'.format(nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_detach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

	@staticmethod
	def wait_for_volume_io_enabled(nvmesh_volume_name):
		try:
			now = datetime.now()
			max_time = datetime.now() + timedelta(seconds=Config.ATTACH_IO_ENABLED_TIMEOUT)
			volume_status = None

			while now <= max_time:
				try:
					volume_status = Utils.get_volume_status(nvmesh_volume_name)
					if volume_status.get("dbg") == '0x200':
						# IO is Enabled
						return True
					else:
						msg = "Waiting for volume {} to have IO Enabled. current status is: 'status':'{}', 'dbg':'{}'"
						Utils.logger.debug(msg.format(nvmesh_volume_name, volume_status.get("status", volume_status.get("dbg"))))
				except IOError as ex:
					# The volume status.json proc file is not ready.
					Utils.logger.debug("Waiting for volume {} to have IO Enabled. Error: ".format(nvmesh_volume_name, ex))
					pass

					time.sleep(1)
					now = datetime.now()
		except Exception as ex:
			import traceback
			tb = traceback.format_exc()
			print(tb)
			raise DriverError(grpc.StatusCode.INTERNAL,
							  "Error while trying to wait_for_volume_io_enabled. Error: {}.\nTraceback: {}".format(ex, tb))

		raise DriverError(grpc.StatusCode.INTERNAL, "Timed-out after waiting {} seconds for volume {} to have IO Enabled. volume status: {}".format(Config.ATTACH_IO_ENABLED_TIMEOUT, nvmesh_volume_name, volume_status))

	@staticmethod
	def get_volume_status(nvmesh_volume_name):
		volume_status_proc = '/proc/nvmeibc/volumes/{}/status.json'.format(nvmesh_volume_name)

		try:
			with open(volume_status_proc) as fp:
				volume_status = json.load(fp)
				return volume_status
		except ValueError:
			Utils.logger.error('Failed to parse JSON from file {}'.format(volume_status_proc))

	@staticmethod
	def verify_nvmesh_access_mode_allowed(current, requested, volume_name):
		if current == requested:
			if current == Consts.AccessMode.SINGLE_NODE_WRITER:
				# We don't allow a new pod to request Exclusive Access when another Pod already has Exclusive Access
				# This will only cause the Pod instantiation to fail, the user should configure the Volume consumer Pods in such a way that only one consumer pod is scheduled on each node.
				# This does not meet the requirement of idempotency. but it prevents a user from causing data corruption by miss-use.
				error_msg = 'Volume {} is already attached with {} ({}) from another Pod'.format(volume_name, Consts.AccessMode.to_nvmesh(current), Consts.AccessMode.to_csi_string(current))
				raise DriverError(grpc.StatusCode.FAILED_PRECONDITION, error_msg)
			else:
				return True
		else:
			error_msg = 'Volume {} is already attached with a different access mode. current access mode: {}, requested: '.format(volume_name, Consts.AccessMode.to_csi_string(current), requested)
			raise DriverError(grpc.StatusCode.FAILED_PRECONDITION, error_msg)

	@staticmethod
	def check_if_access_mode_allowed(requested_nvmesh_access_mode, nvmesh_volume_name):
		if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
			# if this is the first time we are attaching this volume, there is no AccessMode conflict
			return True

		# volume already attached
		vol_status = Utils.get_volume_status(nvmesh_volume_name)
		if vol_status.get('type') != 'visible' or vol_status.get('reservation') == 'Recovery Only':
			# volume is hidden attached
			return True

		current_access_mode = Consts.AccessMode.from_nvmesh(vol_status['reservation'])
		requested_access_mode = Consts.AccessMode.from_nvmesh(requested_nvmesh_access_mode)

		# We need to check if we can change from the current access_mode to the new requested access_mode
		# The following function will throw an Exception if the conversion is not allowed, causing the Stage to fail
		Utils.verify_nvmesh_access_mode_allowed(current=current_access_mode, requested=requested_access_mode, volume_name=nvmesh_volume_name)


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
		print("Looking for a NVMesh Management server using {} from servers {}".format(Config.MANAGEMENT_PROTOCOL, Config.MANAGEMENT_SERVERS))
		while not connected:
			try:
				NVMeshSDKHelper._try_get_sdk_instance()
				connected = ConnectionManager.getInstance().isAlive()
			except ManagementTimeout as ex:
				NVMeshSDKHelper.logger.info("Waiting for NVMesh Management server on {}".format(ConnectionManager.getInstance().managementServer))
				Utils.interruptable_sleep(10)

		print("Connected to NVMesh Management server on {}".format(ConnectionManager.getInstance().managementServer))

	@staticmethod
	def get_management_version():
		err, out = ConnectionManager.getInstance().get('/version')
		if not err:
			version_info = {}
			lines = out.split('\n')
			for line in lines:
				try:
					key_val_pair = line.split('=')
					key = key_val_pair[0]
					value = key_val_pair[1].replace('"','')
					version_info[key] = value
				except:
					pass
			return version_info
		return None

class FeatureSupportChecks(object):
	@staticmethod
	def get_all_features():
		features = {}
		for key, value in FeatureSupport.__dict__.iteritems():
			if not key.startswith('_') and not callable(value):
				features[key] = value

		return features

	@staticmethod
	def is_access_mode_supported():
		exit_code, stdout, stderr = Utils.run_command('python /host/bin/nvmesh_attach_volumes --help | grep -e "--access"', debug=False)
		return exit_code == 0

class FeatureSupport(object):
	AccessMode = FeatureSupportChecks.is_access_mode_supported()