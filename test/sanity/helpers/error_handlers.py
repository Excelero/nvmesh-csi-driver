import subprocess

from grpc import StatusCode
from grpc._channel import _Rendezvous

class ServerUnavailable(Exception):
	def __init__(self, message, sub_exception):
		self.sub_exception = sub_exception
		Exception.__init__(self, message)

def handleGRPCError(action, grpcError):
	if grpcError._state.code == StatusCode.UNAVAILABLE:
		raise ServerUnavailable('The gRPC server is unavailable. is the server running ?', grpcError)
	elif grpcError._state.code in [StatusCode.UNKNOWN, StatusCode.INTERNAL]:
		raise grpcError
	else:
		print('{action} failed with code {code} details: {details}'.format(
			action=action,
			code=grpcError._state.code,
			details=grpcError._state.details))
		raise grpcError

def CatchRequestErrors(func):
	def func_wrapper(*args, **kwargs):
		try:
			func(*args, **kwargs)
		except _Rendezvous as ex:
			handleGRPCError(func.__name__, ex)

	return func_wrapper

def print_docker_logs(container_name):
	try:
		subprocess.check_output(['docker', 'logs', container_name])
	except Exception as ex:
		print(ex)

def CatchNodeDriverErrors(container_name):
	def decorator(func):
		def func_wrapper(*args, **kwargs):
			try:
				func(*args, **kwargs)
			except _Rendezvous as ex:
				print_docker_logs(container_name)
				handleGRPCError(func.__name__, ex)

		return func_wrapper
	return decorator
