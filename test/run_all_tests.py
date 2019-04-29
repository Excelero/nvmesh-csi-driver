#!/usr/bin/env python2
import unittest
from os import path
import sys

from test.helpers.server_manager import ServerManager
from test.clients.identity_client import IdentityClient

project_path = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(project_path)

def runAllTests():
	loader = unittest.TestLoader()
	loader.sortTestMethodsUsing = None
	suite = loader.discover(start_dir='.')
	result = unittest.TextTestRunner(verbosity=2).run(suite)
	return result

def verifyServerIsRunning():
	try:
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		return msg.ready
	except Exception:
		print("Error starting driver gRPC server")
		exit(1)

if __name__ == "__main__":
	driver_server = ServerManager()
	driver_server.start()

	verifyServerIsRunning()

	result = runAllTests()

	driver_server.stop()

	if result.errors:
		exit(1)
