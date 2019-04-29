from grpc import StatusCode
from grpc._channel import _Rendezvous

class ServerUnavailable(Exception):
	def __init__(self, message, sub_exception):
		self.sub_exception = sub_exception
		Exception.__init__(self, message)

def handleGRPCError(action, grpcError):
	if grpcError._state.code == StatusCode.UNAVAILABLE:
		raise ServerUnavailable('The gRPC server is unavailable. did you forget to start the server ?', grpcError)
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
