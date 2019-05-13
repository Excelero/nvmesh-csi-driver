#!/usr/bin/env python2
import os
import sys
import unittest

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.server_manager import ServerManager

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

def run_integration_tests():
	loader = unittest.TestLoader()
	loader.sortTestMethodsUsing = None
	suite = loader.discover(start_dir='.')
	result = unittest.TextTestRunner(verbosity=2).run(suite)
	return result

def verify_server_is_running():
	try:
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		return msg.ready
	except Exception as ex:
		print("Error starting driver gRPC server. ex: {}".format(str(ex)))
		exit(1)

if __name__ == "__main__":

	driver_server = ServerManager()
	driver_server.start()

	verify_server_is_running()

	results = run_integration_tests()

	driver_server.stop()

	print(results)
	if results.errors or results.failures:
		print("Integration Tests Failed")
		exit(1)
