import unittest
from unittest import TestSuite
import time

from driver.common import DriverLogger
from test.helpers.service_manager import ServiceManager
from test.test_controller import TestControllerService
from test.test_identity import TestIdentityService
from test.test_node import TestNodeService

logger = DriverLogger()

class SuiteWithRunningServer(TestSuite):
	def __init__(self, *args, **kwargs):
		TestSuite.__init__(self, *args, **kwargs)
		self.service = ServiceManager(logger)
		self.startServer()

	def __del__(self):
		self.stopServer()

	def startServer(self):
		print('Starting CSI Server')
		self.service.start()
		print('waiting for service to be available')
		time.sleep(0.5)

	def stopServer(self):
		print('stopping CSI server')
		self.service.stop()


def create_suite(testCases=[]):
	suite = SuiteWithRunningServer()

	for testCase in testCases:
		suite.addTest(unittest.makeSuite(testCase))

	return suite

def create_suite_with_all_test():
	all_test_cases = [
		TestIdentityService,
		TestControllerService,
		TestNodeService
	]
	suite = create_suite(all_test_cases)
	return suite

if __name__ == '__main__':
	runner = unittest.TextTestRunner()
	runner.run(create_suite_with_all_test())