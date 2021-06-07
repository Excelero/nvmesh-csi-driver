from multiprocessing import Process

import os
import signal
import time

from driver import consts
from driver.server import NVMeshCSIDriverServer


class ServerManager(object):
	def __init__(self, driverType, mock_node_id=None):
		self.driverType = driverType
		self.mock_node_id = mock_node_id
		self.process = None
		self.pid = -1

	def init_and_start_csi_server(self):
		server = NVMeshCSIDriverServer(self.driverType)
		if self.mock_node_id and self.driverType == consts.DriverType.Node:
			server.node_service.node_id = self.mock_node_id
		server.serve()

	def start(self):
		self.process = Process(target=self.init_and_start_csi_server)
		self.process.start()
		self.pid = int(self.process.pid)
		print('Service started on pid {}'.format(self.pid))

	def stop(self):
		try:
			if self.pid:
				os.kill(int(self.pid), signal.SIGTERM)
		except OSError:
			pass
		finally:
			self.process.join()

	def __del__(self):
		if hasattr(self, 'process') and self.process:
			self.stop()

