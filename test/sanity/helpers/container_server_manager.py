import errno
import json
import logging
import os
import shutil
import subprocess
import sys

import time

log = logging.getLogger('ContainerServerManager')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
log.addHandler(handler)

DEFAULT_CONFIG = {
	'management.protocol': 'https',
	'management.servers': 'mgmt:4000',
	'attachIOEnabledTimeout': '30',
	'printStackTraces': 'false'
}

class ContainerServerManager(object):
	def __init__(self, driver_type, config=None, node_id=None):
		self.driver_type = driver_type
		self.node_id = node_id
		self.container_name = node_id
		self.config = self._get_config_or_default(config)
		self.env_dir = '/tmp/csi_sanity/{}'.format(self.container_name)
		self.csi_socket_path = os.path.join(self.env_dir, 'csi/csi.sock')
		self.version_info = self._get_version_info()
		self.stop_container_on_finish = True
		self._setup_env_dir()
		self._stopped = False


	def keep_container_on_finish(self):
		self.stop_container_on_finish = False

	def _remove_last_container(self):
		try:
			subprocess.check_call(['docker', 'rm', self.container_name])
		except:
			pass

	def start(self):
		log.info('Starting ContainerServerManager {}'.format(self.container_name))
		self._remove_last_container()

		cmd = [
				'docker', 'run', '-d', '--privileged',
				'--cap-add=sys_admin',
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
			'excelero/nvmesh-csi-driver:{}'.format(self.version_info['DRIVER_VERSION'])
		]

		p = subprocess.Popen(cmd)
		stdout, stderr = p.communicate()
		if p.returncode != 0:
			raise ValueError('Error running docker container exit code: {} stdout: {} stderr: {}'.format(p.returncode, stdout, stderr))

		log.info('ContainerServerManager {} Started'.format(self.container_name))
		self._chown_path(self.env_dir)
		return self

	def stream_logs(self):
		# TODO: Implement
		# we could just spawn a new process and call `docker logs container_name --follow`...
		pass

	def stop(self):
		if self.stop_container_on_finish:
			if not self._stopped:
				log.info('Stopping ContainerServerManager {}'.format(self.container_name))
				subprocess.check_call(['docker', 'stop', self.container_name])
				log.info('ContainerServerManager for {} stopped successfully'.format(self.container_name))
				self._stopped = True
		else:
			log.info("Keeping container %s running" % self.container_name)

	def __del__(self):
		self.stop()

	def wait_for_socket(self):
		log.info('Waiting for socket at {}'.format(self.csi_socket_path))
		while not os.path.exists(self.csi_socket_path):
			time.sleep(1)

		log.debug('socket ready at {}'.format(self.csi_socket_path))
		self._chown_path(self.csi_socket_path)
		log.debug('socket chowned at {}'.format(self.csi_socket_path))
		return self

	def _get_version_info(self):
		version_info_output = subprocess.check_output(['/bin/bash', '-c', '../../get_version_info.sh'])
		version_info = {}
		for line in version_info_output.split('\n'):
			if not line:
				continue
			key_value = line.split('=')
			version_info[key_value[0]] = key_value[1]

		return version_info

	def _get_config_or_default(self, config):
		config_copy = DEFAULT_CONFIG.copy()

		if config:
			config_copy.update(config)
		return config_copy

	def set_nvmesh_attach_volumes_content(self, content):
		nvmesh_scripts_dir = os.path.join(self.env_dir, 'host/bin')
		attach_script_path = os.path.join(nvmesh_scripts_dir, 'nvmesh_attach_volumes')
		self._make_sure_dir_exists(nvmesh_scripts_dir)

		with open(attach_script_path, 'w') as fp:
			fp.write(content)

	def set_nvmesh_detach_volumes_content(self, content):
		nvmesh_scripts_dir = os.path.join(self.env_dir, 'host/bin')
		attach_script_path = os.path.join(nvmesh_scripts_dir, 'nvmesh_detach_volumes')
		self._make_sure_dir_exists(nvmesh_scripts_dir)

		with open(attach_script_path, 'w') as fp:
			fp.write(content)

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
		return subprocess.check_call(['sudo', 'chown', '-R', '%s:sudo' % user, path])

	def _rmdir(self, path):
		return subprocess.check_call(['sudo', 'rm', '-rf', path])

	def _setup_env_dir(self):
		self._rmdir(self.env_dir)
		self._make_sure_dir_exists(self.env_dir)
		self._chown_path(self.env_dir)
		self.write_config()
		self.set_nvmesh_attach_volumes_content('print("--access-mode")')
		self.set_nvmesh_detach_volumes_content("raise ValueError('No Content')")

		# Set the topology/zones with the first zone from the topology config
		zones = {}
		topologyConfig = json.loads(self.config['topology'])
		if topologyConfig:
			zone = topologyConfig['zones'].keys()[0]
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