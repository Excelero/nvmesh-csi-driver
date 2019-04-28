#!/usr/bin/env python2
import unittest
from os import path
import sys

from test.helpers.server_manager import ServerManager
from test.clients.identity_client import IdentityClient

project_path = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(project_path)

def runAllTests():
	suite = unittest.TestLoader().discover(start_dir='.')
	res = unittest.TextTestRunner(verbosity=2).run(suite)
	return res

def verifyServerIsRunning():
	try:
		identityClient = IdentityClient()
		msg = identityClient.Probe()
		return msg.ready
	except Exception as ex:
		print("Error starting driver gRPC server")
		exit(1)

if __name__ == "__main__":
	driver_server = ServerManager()
	driver_server.start()

	verifyServerIsRunning()

	res = runAllTests()

	driver_server.stop()

	if res.errors:
		exit(1)
