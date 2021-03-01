from multiprocessing import Process

import os
import signal
import time

from driver import consts
from driver.server import NVMeshCSIDriverServer


class ServerManager(object):
	def __init__(self, driverType, mock_node_id=None):
		self.server = NVMeshCSIDriverServer(driverType)
		if mock_node_id and driverType == consts.DriverType.Node:
			self.server.node_service.node_id = mock_node_id

		self.process = Process(target=self.server.serve)

	def start(self):
		self.process.start()
		print('Service started on pid {}'.format(self.get_pid()))
		print('waiting for service to be available')
		time.sleep(0.5)

	def stop(self):
		if self.get_pid():
			try:
				os.kill(self.get_pid(), signal.SIGTERM)
				self.process.join()
			except OSError:
				pass

	def get_pid(self):
		return int(self.process.pid or 0)

	def __del__(self):
		if hasattr(self, 'process') and self.process:
			self.stop()

