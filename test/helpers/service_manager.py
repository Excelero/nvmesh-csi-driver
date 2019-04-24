from multiprocessing import Process

import os
import signal

from driver.service import NVMeshCSIDriverService


class ServiceManager(object):
	def __init__(self):
		self.server = NVMeshCSIDriverService()
		self.process = Process(target=self.server.serve)

	def start(self):
		self.process.start()
		print('Service started on pid {}'.format(self.get_pid()))

	def stop(self):
		if self.get_pid():
			os.kill(self.get_pid(), signal.SIGTERM)
			self.process.join()

	def get_pid(self):
		return int(self.process.pid or 0)

	def __del__(self):
		self.stop()
