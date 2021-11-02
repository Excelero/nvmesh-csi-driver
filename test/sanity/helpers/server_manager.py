import errno
import logging
from multiprocessing import Process

import os
import signal

from driver import consts
from driver.config import Config
from driver.server import NVMeshCSIDriverServer
from test.sanity.helpers.config_loader_mock import ConfigLoaderMock
from test.sanity.helpers.sanity_log import setup_logging_level

log = logging.getLogger('SanityTests').getChild('ServerManager')

class ServerManager(object):
	def __init__(self, driverType, config=None, mock_node_id=None):
		self.driverType = driverType
		self.mock_node_id = mock_node_id
		self.process = None
		self.pid = -1
		self.config = config

	def init_and_start_csi_server(self, config):
		import driver.config as config_module
		config_module.config_loader = ConfigLoaderMock(config)
		self.make_sure_socket_dir_exists()
		server = NVMeshCSIDriverServer(self.driverType)
		if self.mock_node_id and self.driverType == consts.DriverType.Node:
			server.node_service.node_id = self.mock_node_id
		setup_logging_level()
		server.serve()

	def make_sure_socket_dir_exists(self):
		# remove protocol and file name
		socket_dir = '/'.join(Config.SOCKET_PATH.split('/')[2:-1])
		try:
			os.makedirs(socket_dir)
		except OSError as ex:
			if ex.errno != errno.EEXIST:
				raise

	def start(self):
		self.process = Process(target=self.init_and_start_csi_server, args=(self.config,))
		self.process.start()
		self.pid = int(self.process.pid)
		log.info('Service started on pid {}'.format(self.pid))

	def stop(self):
		try:
			if self.pid:
				log.debug('sending SIGTERM to NVMeshCSIDriverServer with pid {}'.format(self.pid))
				os.kill(self.pid, signal.SIGTERM)
		except OSError:
			pass
		finally:
			self.process.join()

	def __del__(self):
		if hasattr(self, 'process') and self.process:
			self.stop()

