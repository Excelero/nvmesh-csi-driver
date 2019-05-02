from driver.common import Utils, DriverLogger

logger = DriverLogger("FileSystemManager")

class ArgumentError(Exception):
	pass

class FileSystemManager(object):

	@staticmethod
	def create_fake_nvmesh_block_device(nvmesh_volume_name):
		# Creates a Fake block device
		# This function is used for development, for testing with kubernetes on Host that are unable to actually install NVMesh Core Modules
		# TODO: remove when not needed

		block_device_path = '/dev/nvmesh/{}'.format(nvmesh_volume_name)
		cmd = 'mkdir -p /dev/nvmesh/'
		Utils.run_command(cmd)

		cmd = 'dd if=/dev/zero of={} bs=1M count=256'.format(block_device_path)
		Utils.run_command(cmd)

		cmd = 'parted {} mktable gpt'.format(block_device_path)
		Utils.run_command(cmd)

		cmd = 'parted {} mkpart primary 0% 100%'.format(block_device_path)
		Utils.run_command(cmd)

		return block_device_path

	@staticmethod
	def mount(source, target, flags=None):
		flags_str = ' '.join(flags) if flags else ''
		cmd = 'mount {flags_str} {source} {target}'.format(flags_str=flags_str, source=source, target=target)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise Exception("mount failed {} {} {}".format(exit_code, stdout, stderr))

	@staticmethod
	def bind_mount(source, target, flags=None):
		if not flags:
			flags = []

		flags.append('--bind')
		return FileSystemManager.mount(source, target, flags=flags)

	@staticmethod
	def umount(target):
		NOT_MOUNTED = 32
		cmd = 'umount {target}'.format(target=target)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0 and exit_code != NOT_MOUNTED:
			raise Exception("umount failed {} {} {}".format(exit_code, stdout, stderr))

	@staticmethod
	def mkfs(fs_type, target_path, flags=None):
		if not fs_type:
			raise ArgumentError("fs_type argument Cannot be None or an empty string")

		if not flags:
			flags = []

		cmd = "mkfs.{fs_type} {flags} {target_path}".format(fs_type=fs_type, flags=' '.join(flags), target_path=target_path)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise Exception("mkfs failed {} {} {}".format(exit_code, stdout, stderr))