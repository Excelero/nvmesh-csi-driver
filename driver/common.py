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
		LoggerUtils.add_stdout_handler(sdk_logger)

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
		exit_code, stdout, stderr = Utils.run_command('python {}/nvmesh_attach_volumes --wait_for_attach {}'.format(Config.NVMESH_BIN_PATH, nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

	@staticmethod
	def _attach_volume_with_access_mode(nvmesh_volume_name, nvmesh_access_mode):
		preempt_flag = ''
		if Config.USE_PREEMPT and nvmesh_access_mode == Consts.AccessMode.to_nvmesh(Consts.AccessMode.SINGLE_NODE_WRITER):
			preempt_flag = '--preempt'
		cmd_template = 'python {script_dir}/nvmesh_attach_volumes --wait_for_attach --json --access {access} {preempt} {volume}'
		cmd = cmd_template.format(script_dir=Config.NVMESH_BIN_PATH, access=nvmesh_access_mode, preempt=preempt_flag, volume=nvmesh_volume_name)
		exit_code, stdout, stderr = Utils.run_command(cmd)

		try:
			results = json.loads(stdout or stderr)
		except Exception as ex:
			raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: Could not parse output as JSON error_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))

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
				attach_error = volume_res.get('error', None)
				debug_info = "nvmesh_attach_volumes returned volume status: {} error: {} cmd: {}".format(volume_status, volume_res.get('error', None), cmd)
				if attach_error in ['Reservation Mode Denied.', 'Access Mode Denied.'] or volume_status in ['Reservation Mode Denied', 'Access Mode Denied']:
					raise DriverError(grpc.StatusCode.FAILED_PRECONDITION, "Attach Failed - Access Mode Denied - {}".format(debug_info))
				elif volume_status in ['Attached IO Enabled', 'Attached']:
					# Success
					Utils.logger.debug('Volume {} attached with reservation mode {}'.format(nvmesh_volume_name, nvmesh_access_mode))
				elif volume_status == 'Already Attached':
					if 'error' in volume_res:
						raise DriverError(grpc.StatusCode.FAILED_PRECONDITION, "Attach Failed - Already Attached - {}".format(debug_info))
					else:
						Utils.logger.debug('Volume {} is already attached with the requested access mode. output: {}'.format(nvmesh_volume_name, stdout))
				else:
					raise DriverError(grpc.StatusCode.INTERNAL, "Attach Failed - {}".format(debug_info))
			else:
				raise DriverError(grpc.StatusCode.INTERNAL, "nvmesh_attach_volumes failed: Volume {} not found in results. cmd: {} output: {}".format(nvmesh_volume_name, cmd, results))

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
	def call_nvmesh_detach_volume(nvmesh_volume_name):
		exit_code, stdout, stderr = Utils.run_command(
			'python {}/nvmesh_detach_volumes --json {}'.format(Config.NVMESH_BIN_PATH, nvmesh_volume_name))
		if exit_code != 0:
			raise DriverError(grpc.StatusCode.INTERNAL,
							  "nvmesh_detach_volumes failed: exit_code: {} stdout: {} stderr: {}".format(exit_code, stdout, stderr))
		else:
			response = json.loads(stdout or stderr)
			if response["status"] != "success":
				raise DriverError(grpc.StatusCode.INTERNAL, 
									"nvmesh_detach_volumes failed. Got status {}. full response: {}".format(
									response["status"], response))

			volume_status = response["volumes"][nvmesh_volume_name]["status"]
			return volume_status, response

	@staticmethod
	def nvmesh_detach_volume(nvmesh_volume_name, stop_event):
		backoff = BackoffDelayWithStopEvent(stop_event, initial_delay=0.5, factor=2, max_delay=4, max_timeout=15)
		response = None
		while True:
			try:
				volume_status, response = Utils.call_nvmesh_detach_volume(nvmesh_volume_name)
				if volume_status == "Detached":
					# Operation successful
					return
				elif volume_status == "Busy":
					stopped_flag = backoff.wait()
					if stopped_flag:
						raise DriverError(grpc.StatusCode.INTERNAL, 'Stopped nvmesh_detach_volume attempts because Driver is shutting down')
				else:
					# unexpected error returned from nvmesh_detach_volumes
					raise DriverError(grpc.StatusCode.INTERNAL,
									  "nvmesh_detach_volumes failed. Volume status is {}. full response: {}".format(
										  volume_status, response))
			except BackoffTimeoutError:
				raise DriverError(grpc.StatusCode.INTERNAL,
								  "nvmesh_detach_volumes failed after {} seconds and {} attempts. Last error received: {}".format(
									  backoff.get_total_time_seconds(), backoff.num_of_backoffs, response))

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
						Utils.logger.debug(msg.format(nvmesh_volume_name, volume_status.get("status"), volume_status.get("dbg")))
				except IOError as ex:
					# The volume status.json proc file is not ready.
					Utils.logger.debug("Waiting for volume {} to have IO Enabled. Error: {}".format(nvmesh_volume_name, ex))
					pass

				time.sleep(1)
				now = datetime.now()
		except Exception as ex:
			Utils.logger.exception(ex)
			raise DriverError(grpc.StatusCode.INTERNAL, "Error while trying to wait_for_volume_io_enabled. Error: {}.".format(ex))

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



class FeatureSupportChecks(object):
	@staticmethod
	def calculate_all_feature_support():
		FeatureSupport.AccessMode = FeatureSupportChecks.is_access_mode_supported()

	@staticmethod
	def get_all_features():
		features = {}
		for key, value in FeatureSupport.__dict__.iteritems():
			if not key.startswith('_') and not callable(value):
				features[key] = value

		return features

	@staticmethod
	def is_access_mode_supported():
		if os.environ.get('DEVELOPMENT'):
			return True
		attach_script_path = '{}/nvmesh_attach_volumes'.format(Config.NVMESH_BIN_PATH)
		while not os.path.exists(attach_script_path):
			print('Waiting for attach script to be available under {}'.format(attach_script_path))
			time.sleep(5)
		exit_code, stdout, stderr = Utils.run_command('python {} --help | grep -e "access"'.format(attach_script_path))
		return exit_code == 0

class FeatureSupport(object):
	AccessMode = None

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