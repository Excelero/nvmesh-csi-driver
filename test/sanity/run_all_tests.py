#!/usr/bin/env python2
import os
import sys
import unittest

from driver import consts, config
from test.sanity.helpers import config_loader_mock
config.config_loader = config_loader_mock.ConfigLoaderMock()

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.server_manager import ServerManager

project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

def run_sanity_tests():
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
	results = run_sanity_tests()

	print(results)
	if results.errors or results.failures:
		print("Sanity Tests Failed")
		exit(1)
