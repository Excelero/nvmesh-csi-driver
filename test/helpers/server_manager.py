import logging
from multiprocessing import Process

import os
import signal
import time

from driver.server import NVMeshCSIDriverServer


class ServerManager(object):
	def __init__(self, logger=None):
		if not logger:
			logger = logging.getLogger("NVMeshCSIDriverServer")
		self.server = NVMeshCSIDriverServer(logger)
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
		self.stop()

if __name__ == "__main__":
	mgr = ServerManager()

	def sig_term_handler(signum, frame):
		mgr.stop()

	signal.signal(signal.SIGTERM, sig_term_handler)
	signal.signal(signal.SIGINT, sig_term_handler)

	mgr.start()

