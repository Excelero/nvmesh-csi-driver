import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
import grpc

from config import Config
import consts as Consts
from sdk_helper import NVMeshSDKHelper


class ServerLoggingInterceptor(grpc.ServerInterceptor):
	def __init__(self, logger):
		self.logger = logger

	def intercept_service(self, continuation, handler_call_details):
		# gRPC Python doesn't have a complete server interceptor implementation that allow you to access the request obj
		# but we can print the method's name
		method = handler_call_details.method.split('/')[-1:][0]
		self.logger.debug('called method {}'.format(method))
		return continuation(handler_call_details)

class LoggerUtils(object):
	@staticmethod
	def init_root_logger():
		root_logger = logging.getLogger()
		root_logger.setLevel(logging.getLevelName(Config.LOG_LEVEL or 'DEBUG'))
		LoggerUtils.add_stdout_handler(root_logger)
		return root_logger

	@staticmethod
	def init_sdk_logger():
		sdk_logger = logging.getLogger('NVMeshSDK')
		sdk_logger.setLevel(logging.getLevelName(Config.SDK_LOG_LEVEL or 'DEBUG'))

	@staticmethod
	def _get_default_formatter():
		formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
		return formatter

	@staticmethod
	def _add_handler(logger, handler):
		handler.setLevel(logger.level)
		formatter = LoggerUtils._get_default_formatter()
		handler.setFormatter(formatter)
		logger.addHandler(handler)

	@staticmethod
	def add_stdout_handler(logger):
		handler = logging.StreamHandler(sys.stdout)
		LoggerUtils._add_handler(logger, handler)

def CatchServerErrors(func):
	def func_wrapper(self, request, context):
		try:
			return func(self, request, context)
		except DriverError as drvErr:
			self.logger.warning("Driver Error caught in gRPC call {} - Code: {} Message:{}".format(func.__name__, str(drvErr.code), str(drvErr.message)))
			self.logger.exception("Driver Error with stack trace")
			context.abort(drvErr.code, str(drvErr.message))

		except Exception as ex:
			if Config.PRINT_STACK_TRACES:
				self.logger.exception("Error caught in gRPC call  {} - {}".format(func.__name__, ex))
			else:
				self.logger.warning("Error caught in gRPC call {} - {}".format(func.__name__, ex))

			context.abort(grpc.StatusCode.INTERNAL, str(ex))

	return func_wrapper

class DriverError(Exception):
	def __init__(self, code, message):
		Exception.__init__(self, message)
		self.code = code

class Utils(object):
	logger = logging.getLogger("Utils")

	GB_TO_BYTES = pow(2.0, 30)

	@staticmethod
	def format_as_GiB(bytes_as_int):
		gib = bytes_as_int / Utils.GB_TO_BYTES
		# This will round the nubmer and display up to 1 decimal point - only if he nuber is not round.
		return "{1:0.{0}f}GiB".format(int(gib % 1 > 0), gib)

	@staticmethod
	def hide_secrets_from_message(req_json):
		req_obj = json.loads(req_json)
		secrets = req_obj.get('secrets')
		if secrets:
			for secret_name in secrets.keys():
				secrets[secret_name] = "<removed-from-log>"
		return json.dumps(req_obj, indent=4)

	@staticmethod
	def volume_id_to_nvmesh_name(co_vol_name):
		# NVMesh volume name / id cannot be longer than 23 characters
		return 'csi-' + co_vol_name[4:22]

	@staticmethod
	def is_nvmesh_volume_attached(nvmesh_volume_name):
		cmd = 'ls /dev/nvmesh/{}'.format(nvmesh_volume_name)
		exit_code, stdout, stderr = Utils.run_command(cmd, debug=False)
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
	def run_safe_command(cmd, input=None, debug=True):
		# This function prevents shell injection attacks when the command includes input from the user
		# for example when parsing StorageClass parameters as flags for a shell command
		# cmd is a list where the first item is the command and the rest are arguments
		if debug:
			Utils.logger.debug("running: {}".format(' '.join(cmd)))
			
		p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=PIPE)
		stdout, stderr = p.communicate(input=input)
		exit_code = p.returncode
		if debug:
			Utils.logger.debug("cmd: {} return exit_code={} stdout={} stderr={}".format(' '.join(cmd), exit_code, stdout, stderr))
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
	def nvmesh_attach_volume_rest_call(client_id, client_api, nvmesh_volume_name, requested_nvmesh_access_mode, reservation_version=None, retries_left=1):
		Utils.logger.debug('nvmesh_attach_volume_rest_call Volume {} doing attach REST call to management'.format(nvmesh_volume_name))

		err, res = client_api.attach(client_id, nvmesh_volume_name, requested_nvmesh_access_mode, reservation_version=reservation_version)
		# example: [{"_id": "vol1", "success": false, "error": "There is no such client client-1 or attachment", "payload": null}]

		try:
			res = res[0]
			if res["success"]:
				# operation successful
				return
			else:
				err = res["error"].lower()
				Utils.logger.debug('NVMesh attach failed for volume {} Error: {}'.format(nvmesh_volume_name, err))

				if 'already attached' in err:
					# Already attached - Idempotent => return true
					Utils.logger.debug('Volume {} is already attached with the requested access mode. output: {}'.format(nvmesh_volume_name, res))
					return
				elif 'access mode denied' in err \
					or 'the requested RM doesn\'t comply with the volume RM'.lower() in err:
					msg = "NVMesh attach access mode denied for {} (NVMesh \"{}\"). Error: {}".format(
						Consts.AccessMode.nvmesh_to_k8s_string(requested_nvmesh_access_mode), requested_nvmesh_access_mode, err)
					raise DriverError(grpc.StatusCode.FAILED_PRECONDITION, msg)
				elif 'reservation version is outdated' in err and retries_left > 0:
					Utils.logger.debug('Attach returned {} we will retry with the updated reservation version'.format(err, nvmesh_volume_name))
					# TODO: the mgmt should send the updated reservation as a separate int field, but for now we have to parse the string.
					reservation_version = int(err.split(':')[1].strip())
					Utils.nvmesh_attach_volume_rest_call(client_id, client_api, nvmesh_volume_name, requested_nvmesh_access_mode, reservation_version, retries_left-1)
				else:
					raise DriverError(grpc.StatusCode.INTERNAL, "NVMesh Attach Failed - {}".format(err))
		except DriverError:
			raise
		except Exception as ex:
			err = "Failed to parse attach response from the management. error: {} message received: {}".format(ex, res)
			raise DriverError(grpc.StatusCode.INTERNAL, "Attach Failed - {}".format(err))

	@staticmethod
	def nvmesh_attach_volume(client_id, client_api, nvmesh_volume_name, requested_nvmesh_access_mode):
		Utils.check_if_access_mode_allowed(requested_nvmesh_access_mode, nvmesh_volume_name)
		Utils.nvmesh_attach_volume_rest_call(client_id, client_api, nvmesh_volume_name, requested_nvmesh_access_mode)

	@staticmethod
	def nvmesh_detach_volume_rest_call(client_id, client_api, nvmesh_volume_name, force):
		err, res = client_api.detach(client_id, nvmesh_volume_name, force)
		# example: [{"_id": "vol1", "success": false, "error": "There is no such client client-1 or attachment", "payload": null}]
		try:
			res = res[0]
			if res["success"]:
				# operation successful
				return
			else:
				err = res["error"].lower()
				if 'there is no such client' in err:
					# Already detached - Idempotent => return true
					Utils.logger.debug('Volume {} is already detached with the requested access mode. output: {}'.format(nvmesh_volume_name, res))
					return
				else:
					raise DriverError(grpc.StatusCode.INTERNAL, "Detach Failed - {}".format(res))
		except Exception as ex:
			raise DriverError(grpc.StatusCode.INTERNAL, "Failed to parse detach response: {} Error: {}".format(res, ex))

	@staticmethod
	def wait_for_volume_to_detach(nvmesh_volume_name, stop_event):
		backoff = BackoffDelayWithStopEvent(stop_event, initial_delay=0.2, factor=2, max_delay=1, max_timeout=Config.DETACH_TIMEOUT)
		detached = False
		while not detached:
			try:
				if not Utils.is_nvmesh_volume_attached(nvmesh_volume_name):
					detached = True
				else:
					stopped_flag = backoff.wait()
					if stopped_flag:
						raise DriverError(grpc.StatusCode.INTERNAL, 'Stopped nvmesh_detach_volume attempts because Driver is shutting down')
			except BackoffTimeoutError:
				raise DriverError(grpc.StatusCode.INTERNAL,
								  "timed out waiting for volume {} to detach after {} seconds and {} attempts.".format(
									  nvmesh_volume_name, backoff.get_total_time_seconds(), backoff.num_of_backoffs))

		Utils.logger.debug('Volume {} successfully detached and device removed from the host'.format(nvmesh_volume_name))

	@staticmethod
	def nvmesh_detach_volume(client_id, client_api, nvmesh_volume_name, force, stop_event):
		Utils.nvmesh_detach_volume_rest_call(client_id, client_api, nvmesh_volume_name, force)
		Utils.wait_for_volume_to_detach(nvmesh_volume_name, stop_event)

	@staticmethod
	def wait_for_volume_io_enabled(nvmesh_volume_name):
		backoff = BackoffDelay(initial_delay=1, factor=1, max_timeout=Config.ATTACH_IO_ENABLED_TIMEOUT)
		volume_status = None

		while True:
			try:
				try:
					volume_status = Utils.get_volume_status(nvmesh_volume_name)
					if volume_status.get("dbg") == '0x200':
						# IO is Enabled
						return True
					else:
						msg = "Waiting for volume {} to have IO Enabled. current status is: 'status':'{}', 'dbg':'{}'"
						Utils.logger.debug(msg.format(nvmesh_volume_name, volume_status.get("status"), volume_status.get("dbg")))
				except IOError as ex:
					# The volume status.json proc file is not ready.
					Utils.logger.debug("Waiting for volume {} to have IO Enabled. Error: {}".format(nvmesh_volume_name, ex))
					pass

				backoff.wait()
			except BackoffTimeoutError:
				raise DriverError(grpc.StatusCode.INTERNAL, "Timed-out after waiting {} seconds for volume {} to have IO Enabled. volume status: {}".format(
					Config.ATTACH_IO_ENABLED_TIMEOUT,
					nvmesh_volume_name,
					json.dumps(volume_status)))

	@staticmethod
	def get_volume_status(nvmesh_volume_name):
		volume_status_proc = '/proc/nvmeibc/volumes/{}/status.json'.format(nvmesh_volume_name)
		if 'SIMULATED_PROC' in os.environ:
			volume_status_proc = os.path.join('/simulated{}'.format(volume_status_proc))

		try:
			with open(volume_status_proc) as fp:
				volume_status = json.load(fp)
				return volume_status
		except ValueError as ex:
			Utils.logger.error('Failed to parse JSON from file {}'.format(volume_status_proc))
			raise ValueError('Failed to parse JSON from file {}'.format(volume_status_proc))

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
		try:
			vol_status = Utils.get_volume_status(nvmesh_volume_name)
			if vol_status.get('type') != 'visible' or vol_status.get('reservation') == 'Recovery Only':
				# volume is hidden attached
				return True
		except (ValueError, IOError) as ex:
			raise DriverError(grpc.StatusCode.INTERNAL, 'Failed to run check_if_access_mode_allowed. %s' % ex)

		current_access_mode = Consts.AccessMode.from_nvmesh(vol_status['reservation'])
		requested_access_mode = Consts.AccessMode.from_nvmesh(requested_nvmesh_access_mode)

		# We need to check if we can change from the current access_mode to the new requested access_mode
		# The following function will throw an Exception if the conversion is not allowed, causing the Stage to fail
		Utils.verify_nvmesh_access_mode_allowed(current=current_access_mode, requested=requested_access_mode, volume_name=nvmesh_volume_name)

	@staticmethod
	def sanitize_json_object_keys(jsonObj):
		if isinstance(jsonObj, dict):
			for key in jsonObj.keys():
				sanitized = Utils.sanitize_json_key(key)
				if sanitized != key:
					jsonObj[sanitized] = jsonObj[key]
					del jsonObj[key]
		elif isinstance(jsonObj, list):
			for index, item in enumerate(jsonObj):
				jsonObj[index] = Utils.sanitize_json_object_keys(item)

		return jsonObj

	@staticmethod
	def sanitize_json_key(key):
		return key.replace('.','-')

	@staticmethod
	def nvmesh_vol_name_to_co_id(nvmesh_vol_name, zone):
		if zone:
			return zone + ':' + nvmesh_vol_name
		else:
			return nvmesh_vol_name

	@staticmethod
	def zone_and_vol_name_from_co_id(volume_handle_id):
		parts = volume_handle_id.split(':')
		if len(parts) == 2:
			return parts[0], parts[1]
		if len(parts) == 1:
			return None, parts[0]

	@staticmethod
	def parseBoolean(value):
		if type(value) == bool:
			return value
		elif type(value) == str or type(value) == unicode:
			return value.lower() == 'true'

		raise ValueError('Failed to parse boolean from %s with type %s' % (value, type(value)))

	@staticmethod
	def get_volume_stats(volume_path):
		if len(volume_path) == 0:
			raise DriverError(grpc.StatusCode.INVALID_ARGUMENT, 'Volume path cannot be empty')

		try:
			# see https://man7.org/linux/man-pages/man3/statvfs.3.html for details
			info = os.statvfs(volume_path)
			stats = {
				"available_bytes": info.f_bavail * info.f_bsize,
				"total_bytes": info.f_blocks * info.f_bsize,
				"used_bytes": (info.f_blocks - info.f_bfree) * info.f_bsize,
				"available_inodes": info.f_ffree,
				"total_inodes": info.f_files,
				"used_inodes": info.f_files - info.f_ffree,
			}

			return stats
		except OSError:
			raise DriverError(grpc.StatusCode.INTERNAL, 'node-driver unable to reach the volume path')

class BackoffTimeoutError(Exception):
	pass

'''
Helper for a back-off mechanism to allow repeated action with an increasing delay after each failure
Parameters:
initial_delay - The delay in the first iteration
factor - The factor in which the delay changes every iteration. 
max_delay - the maximum delay 
max_timeout - The timeout for the entire operation in all iterations

A factor value of 1 means the delay is the same every iteration, 
a factor value of 2 means the delay is doubled every iteration until it reaches max_delay 
and keeps the max_delay until max_timeout is reached

'''
class BackoffDelay(object):
	def __init__(self, initial_delay, factor, max_delay=None, max_timeout=None):
		self.initial_delay = initial_delay
		self.factor = factor
		self.max_delay = max_delay
		self.max_timeout = max_timeout
		self.current_delay = self.initial_delay
		self.start_time = datetime.now()
		self.num_of_backoffs = 0

	def wait(self):
		if self.max_timeout and self.get_total_time_seconds() > self.max_timeout:
			raise BackoffTimeoutError('Backoff timed out reached')

		self.num_of_backoffs += 1
		time.sleep(self.current_delay)
		self.calculate_next_delay()

	def get_total_time_seconds(self):
		return (datetime.now() - self.start_time).seconds

	def calculate_next_delay(self):
		self.current_delay = self.current_delay * self.factor

		if self.max_delay:
			self.current_delay = min(self.max_delay, self.current_delay)

	def reset(self):
		self.current_delay = self.initial_delay
		self.start_time = datetime.now()
		self.num_of_backoffs = 0

	def is_reset(self):
		return self.current_delay == self.initial_delay

'''
Helper for a back-off mechanism using the threading.Event() wait() method which will exit when the event is set
'''
class BackoffDelayWithStopEvent(BackoffDelay):
	''
	def __init__(self, event, initial_delay, factor, max_delay=None, max_timeout=None):
		self.event = event
		super(BackoffDelayWithStopEvent, self).__init__(initial_delay, factor, max_delay, max_timeout)

	def wait(self):
		if self.max_timeout and self.get_total_time_seconds() + self.current_delay > self.max_timeout:
			raise BackoffTimeoutError('Backoff timed out reached')

		self.num_of_backoffs += 1
		event_flag = self.event.wait(self.current_delay)
		self.calculate_next_delay()
		return event_flag