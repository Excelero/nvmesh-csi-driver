import grpc

class ClientLoggingInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.StreamUnaryClientInterceptor):

	def __init__(self, logger):
		self.logger = logger

	def _intercept_call(self, continuation, client_call_details, request_or_iterator):
		method = client_call_details.method.split('/')[-1:][0]
		from google.protobuf.json_format import MessageToJson
		jsonObj = MessageToJson(request_or_iterator, indent=None)
		self.logger.debug('calling method {} with parameters {}'.format(method, jsonObj))
		return continuation(client_call_details, request_or_iterator)

	def intercept_unary_unary(self, continuation, client_call_details, request):
		return self._intercept_call(continuation, client_call_details, request)

	def intercept_stream_unary(self, continuation, client_call_details,
							   request_iterator):
		return self._intercept_call(continuation, client_call_details,
									request_iterator)