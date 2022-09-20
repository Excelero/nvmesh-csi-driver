import errno
import json
import logging
import os
import subprocess

import time

from test.sanity.clients.identity_client import IdentityClient
from test.sanity.helpers.config_loader_mock import get_version_info

sanity_logger = logging.getLogger('SanityTests')
log = sanity_logger.getChild('ContainerdDriver')

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
		self.logger = log.getChild(self.container_name)
		self.config = self._get_config_or_default(config)
		self.env_dir = '/tmp/csi_sanity/{}'.format(self.container_name)
		self.csi_socket_path = os.path.join(self.env_dir, 'csi/csi.sock')
		self.version_info = get_version_info()
		self.stop_container_on_finish = True
		self._setup_env_dir()
		self._stopped = False
		self.image_name_with_tag = None

	def keep_container_on_finish(self):
		self.stop_container_on_finish = False

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
		self.logger.info('Starting ContainerServerManager {}'.format(self.container_name))
		self._remove_last_container()

		self.image_name_with_tag = 'excelero/nvmesh-csi-driver:{}'.format(self.version_info['DRIVER_VERSION'])

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
			self.image_name_with_tag
		]

		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = p.communicate()

		if p.returncode != 0:
			self.handle_docker_errors(cmd, p.returncode, stdout, stderr)

		self.logger.info('ContainerServerManager {} Started'.format(self.container_name))
		self._chown_path(self.env_dir)
		return self

	def handle_docker_errors(self, command, exit_code, stdout, stderr):
		if 'Unable to find image' in stderr:
			raise ValueError('Image {} not found. please run `make build` in the project root to build the image locally'.format(self.image_name_with_tag))
		else:
			raise ValueError('Error running docker container  command: {} exit code: {} stdout: {} stderr: {}'.format(' '.join(command), exit_code, stdout, stderr))

	def stream_logs(self):
		# TODO: Implement
		# we could just spawn a new process and call `docker logs container_name --follow`...
		pass

	def run_command_in_container(self, cmd, **kwargs):
		return subprocess.check_output(['docker', 'exec', self.container_name] + cmd, **kwargs)

	def stop(self):
		if self.stop_container_on_finish:
			if not self._stopped:
				self.logger.info('Stopping')
				try:
					subprocess.check_call(['docker', 'stop', self.container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				except subprocess.CalledProcessError as ex:
					self.logger.warning('docker stop command failed')

				self.logger.info('stopped successfully')
				self._stopped = True
		else:
			self.logger.info("Keeping container running")

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
		return subprocess.check_call(['sudo', 'chown', '-R', '%s' % user, path])

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


class NVMeshAttachScriptMockBuilder(object):
	"""
	This class is a builder to create code for nvmesh_attach_volumes that will run inside the container
	Which would simulate the script, the device file, and the proc file
	"""
	IO_ENABLED = '0x200'
	ATTACHED_IO_ENABLED = "Attached IO Enabled"

	def __init__(self):
		self.create_proc_file = True
		self.create_device_file = True
		self.proc_dbg_value = NVMeshAttachScriptMockBuilder.IO_ENABLED
		self.res_volume_status = NVMeshAttachScriptMockBuilder.ATTACHED_IO_ENABLED
		self.expect_preempt = False

		self.expected_argument = None
		self.not_expected_argument = None

	def getDefaultSuccessBehavior(self):
		return self.compile()

	def setDbgValue(self, dbg_value):
		self.proc_dbg_value = dbg_value
		return self

	def noProcFile(self):
		self.create_proc_file = False
		return self

	def noDeviceFile(self):
		self.create_device_file = False
		return self

	def setVolumeStatus(self, volume_status):
		self.res_volume_status = volume_status
		return self

	def makeSureArgumentExists(self, expected_argument):
		self.expected_argument = expected_argument
		return self

	def makeSureArgumentDoesNotExist(self, not_expected_argument):
		self.not_expected_argument = not_expected_argument
		return self

	def compile(self):
		code = """
import sys
import json
import os

MB = 1024 * 1024
GB = MB * 1024
vol_id = sys.argv[-1]
"""
		if self.expected_argument:
			code += """
if '{expected_argument}' not in sys.argv:
	raise ValueError('Expected {expected_argument} flag when AccessMode is Exclusive (ReadWriteOnce). argv=%s' % sys.argv)
""".format(expected_argument=self.expected_argument)

		if self.not_expected_argument:
			code += """
if '{not_expected_argument}' in sys.argv:
	raise ValueError('Not expecting {not_expected_argument} flag when the Config.preempt flag is set to false. argv=%s' % sys.argv)
""".format(not_expected_argument=self.not_expected_argument)

		if self.create_device_file:
			code += """
device_path = "/dev/nvmesh/%s" % vol_id
with open(device_path, "wb") as f:
	f.truncate(MB * 100)
"""

		# Add code to simulate a /proc/nvmeibc
		if self.create_proc_file:
			code += """
proc_dir = '/simulated/proc/nvmeibc/volumes/%s'  % vol_id
proc_status_file = "%s/status.json" % proc_dir

try:
	os.makedirs(proc_dir)
except:
	pass
with open(proc_status_file, "w") as f:
	proc_content_dict = {{
		'dbg':'{dbg_value}'
	}}
	f.write(json.dumps(proc_content_dict))
""".format(dbg_value=self.proc_dbg_value)

		# Add code to
		code += """
	print('{{ "status": "success", "volumes": {{ "%s": {{ "status": "{volume_status}" }} }} }}' % vol_id)
""".format(volume_status=self.res_volume_status)

		return code



class NVMeshDetachScriptMockBuilder(object):
	"""
	This class is a builder to create code for nvmesh_detach_volumes that will run inside the container
	Which would simulate the script, the device file, and the proc file
	"""
	DETACHED = "Detached"

	def __init__(self):
		self.code = self._getDefaultCode()
		self.vol_status = "Detached"

	def _getDefaultCode(self):
		return """
import sys
import os
import json

vol_id = sys.argv[-1]
vol_status = "{vol_status}"
if vol_status == "Detached":
	device_path = "/dev/nvmesh/%s" % vol_id
	os.remove(device_path)

response = {{
	"status": "success",
	"volumes": {{
		vol_id: {{ 
			"status": vol_status
		}}
	}}
}}

print(json.dumps(response))
"""

	def getDefaultSuccessBehavior(self):
		self.vol_status = "Detached"
		return self.compile()

	def returnBusy(self):
		self.vol_status = "Busy"
		return self
		
	def compile(self):
		return self.code.format(vol_status=self.vol_status)