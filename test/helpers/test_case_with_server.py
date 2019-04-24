import unittest

import time

from test.helpers.service_manager import ServiceManager


class TestCaseWithServerRunning(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		print('set up')
		cls.service = ServiceManager()
		cls.service.start()
		print('waiting for service to be available')
		time.sleep(2)

	@classmethod
	def tearDownClass(cls):
		print('tear down')
		cls.service.stop()