import errno
import json
import logging
import os
import subprocess

import time
from threading import Thread

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.config_loader_mock import get_version_info

sanity_logger = logging.getLogger('SanityTests')
log = sanity_logger.getChild('ContainerdDriver')

DEFAULT_CONFIG = {
	'management.protocol': 'https',
	'management.servers': 'mgmt:4000',
	'attachIOEnabledTimeout': '30',
	'printStackTraces': 'true'
}

class ContainerizedCSIDriver(object):

	def __init__(self, driver_type, config=None, node_id=None):
		self.driver_type = driver_type
		self.node_id = node_id
		self.container_name = node_id
		self.logger = log.getChild(self.container_name)
		self.config = self._get_config_or_default(config)
		self.env_dir = '/tmp/csi_sanity/{}'.format(self.container_name)
		self.csi_socket_path = os.path.join(self.env_dir, 'csi/csi.sock')
		self.version_info = get_version_info()
		self._setup_env_dir()
		self._stopped = False
		self.image_name_with_tag = None
		self.stdout = []

	def _remove_last_container(self):
		try:
			subprocess.check_call(['docker', 'stop', self.container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except:
			pass

		try:
			subprocess.check_call(['docker', 'rm', self.container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		except:
			pass

	def start(self):
		self.logger.info('Starting ContainerizedCSIDriver {}'.format(self.container_name))
		self._remove_last_container()

		self.image_name_with_tag = 'excelero/nvmesh-csi-driver:{}'.format(self.version_info['DRIVER_VERSION'])

		cmd = [
			'docker', 'run', '-d', '--privileged',
			'--cap-add=sys_admin',
			'--net', 'csi_test',
			'--name', self.container_name,
			'-h', self.node_id,
			'-v', '{}/topology:/topology'.format(self.env_dir),
			'-v', '{}/config:/config'.format(self.env_dir),
			'-v', '{}/csi:/csi'.format(self.env_dir),
			'-v', '{}/var/lib/kubelet:/var/lib/kubelet'.format(self.env_dir),
			'-v', '{}/dev/nvmesh:/dev/nvmesh'.format(self.env_dir),
			'-v', '{}/host/bin/:/host/bin'.format(self.env_dir),
			'-v', '{}/var/opt/NVMesh:/var/opt/NVMesh'.format(self.env_dir),
			'-v', '{}/opt/NVMesh:/opt/NVMesh'.format(self.env_dir),
			'-v', '{}/proc/nvmeibc:/simulated/proc/nvmeibc'.format(self.env_dir),
			'-e', 'DRIVER_TYPE={}'.format(self.driver_type),
			'-e', 'DRIVER_NAME={}'.format('nvmesh-csi.excelero.com'),
			'-e', 'SOCKET_PATH={}'.format('unix:///csi/csi.sock'),
			'-e', 'MANAGEMENT_SERVERS=a.b:4000',
			'-e', 'SIMULATED_PROC=True',
			'-p', '5050',
			self.image_name_with_tag
		]

		csi_driver_logger = self.logger.getChild("CSI")
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		csi_driver_logger.info("Started")
		self.logs_thread = self.stream_output_in_a_thread(p)

		self.logger.info('ContainerizedCSIDriver {} Started'.format(self.container_name))
		self._chown_path(self.env_dir)

		return self

	def stream_output_in_a_thread(self, p):

		def stream_logs(pipe, logger):
			for line in iter(pipe.readline, b''):
				logger.info(line)
				for h in logger.handlers:
					h.flush()
				self.stdout.append(line)
			logger.info('finished reading output')
			p.wait()
			logger.debug('Cluster ended with exit code: {}'.format(p.returncode))
			if p.returncode != 0:
				if p.returncode == -15:
					logger.info('Server was stopped')
				else:
					logger.error('Cluster ended with an error (exit code %d). exiting..' % p.returncode)

			logger.info('Cluster stopped')
			self.stopped = True

		t = Thread(name='{}_stream_logs'.format(self.container_name), target=stream_logs, args=(p.stdout, self.logger))
		t.start()
		return t

	def handle_docker_errors(self, command, exit_code, stdout, stderr):
		if 'Unable to find image' in stderr:
			raise ValueError('Image {} not found. please run `make build` in the project root to build the image locally'.format(self.image_name_with_tag))
		else:
			raise ValueError('Error running docker container  command: {} exit code: {} stdout: {} stderr: {}'.format(' '.join(command), exit_code, stdout, stderr))

	def run_command_in_container(self, cmd, **kwargs):
		return subprocess.check_output(['docker', 'exec', self.container_name] + cmd, **kwargs)

	def stop(self):
		self.logger.info('Joining logs_thread')
		self.logs_thread.join()
		if not self._stopped:
			self.logger.info('Stopping')
			try:
				subprocess.check_call(['docker', 'stop', self.container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			except subprocess.CalledProcessError as ex:
				self.logger.warning('docker stop command failed')

			self.logger.info('stopped successfully')
			self._stopped = True

	def __del__(self):
		if not self._stopped:
			self.stop()

	def wait_for_socket(self):
		self.logger.info('Waiting for socket at {}'.format(self.csi_socket_path))
		while not os.path.exists(self.csi_socket_path):
			time.sleep(0.5)

		self.logger.debug('socket ready at {}'.format(self.csi_socket_path))
		self._chown_path(self.csi_socket_path)
		self.logger.debug('socket chowned at {}'.format(self.csi_socket_path))

	def wait_for_grpc_server_to_be_alive(self):
		self.wait_for_socket()

		grpc_ready = False
		client = IdentityClient(socket_path='unix://' + self.csi_socket_path)

		while not grpc_ready:
			try:
				client.GetPluginInfo()
				grpc_ready = True
			except Exception as ex:
				time.sleep(0.5)
		return self

	def _get_config_or_default(self, config):
		config_copy = DEFAULT_CONFIG.copy()

		if config:
			config_copy.update(config)
		return config_copy

	def write_config(self):
		# This will write the config as a mounted kubernetes ConfigMap (file per field)
		config_dir = os.path.join(self.env_dir, 'config')
		self._make_sure_dir_exists(config_dir)
		for field_name, value in self.config.items():
			config_file = os.path.join(config_dir, field_name)
			with open(config_file, 'w') as fp:
				fp.write(value or "")

	def set_topology_config_map(self, zones_json):
		# This will write the config as a mounted kubernetes ConfigMap (file per field)
		topology_config_map_dir = os.path.join(self.env_dir, 'topology')
		self._make_sure_dir_exists(topology_config_map_dir)
		zones_file = os.path.join(topology_config_map_dir, 'zones')

		with open(zones_file, 'w') as fp:
			fp.write(zones_json)

	def _make_sure_dir_exists(self, dir):
		try:
			os.makedirs(dir)
		except OSError as ex:
			if ex.errno != errno.EEXIST:
				raise

	def make_dir_in_env_dir(self, dir_path):
		if dir_path[0] == '/':
			dir_path = dir_path[1:]
		dir_in_env = os.path.join(self.env_dir, dir_path)
		self._make_sure_dir_exists(dir_in_env)

	def _chown_path(self, path):
		import getpass
		user = getpass.getuser()
		return subprocess.check_call(['sudo', 'chown', '-R', '%s' % user, path])

	def _rmdir(self, path):
		return subprocess.check_call(['sudo', 'rm', '-rf', path])

	def _setup_env_dir(self):
		self._rmdir(self.env_dir)
		self._make_sure_dir_exists(self.env_dir)
		self._chown_path(self.env_dir)
		self.write_config()

		# Set the topology/zones with the first zone from the topology config
		zones = {}
		topology_config = json.loads(self.config['topology'])
		if topology_config:
			zone = topology_config['zones'].keys()[0]
			zones[zone] = {'nodes': [self.node_id]}
			self.set_topology_config_map(json.dumps(zones))


	def add_nvmesh_device(self, volume_id):
		dev_nvmesh = os.path.join(self.env_dir, 'dev/nvmesh')
		device_file = os.path.join(dev_nvmesh, volume_id)

		self._make_sure_dir_exists(dev_nvmesh)
		if not os.path.isfile(device_file):
			with open(device_file, 'w') as fp:
				fp.write('')

	def remove_nvmesh_device(self, volume_id):
		dev_nvmesh = os.path.join(self.env_dir, 'dev/nvmesh')
		device_file = os.path.join(dev_nvmesh, volume_id)
		os.remove(device_file)