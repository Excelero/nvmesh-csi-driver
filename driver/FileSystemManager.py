import logging
import shutil

from grpc import StatusCode

from common import Utils, DriverError
import consts as Consts

logger = logging.getLogger("FileSystemManager")

class ArgumentError(Exception):
	pass

class MountError(Exception):
	pass

class MountTargetIsBusyError(MountError):
	pass

class FileSystemManager(object):

	@staticmethod
	def is_mounted(mount_path):
		cmd = 'grep -qs "{} " /proc/mounts'.format(mount_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return exit_code == 0

	@staticmethod
	def mount(source, target, flags=None, mount_options=None):
		flags_str = ' '.join(flags) if flags else ''
		mount_opts_str = '-o ' + ','.join(mount_options) if mount_options else ''
		cmd = 'mount {flags_str} {options} {source} {target}'.format(flags_str=flags_str, options=mount_opts_str, source=source, target=target)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise Exception("mount failed {} {} {}".format(exit_code, stdout, stderr))

	@staticmethod
	def bind_mount(source, target, flags=None, mount_options=None):
		flags = flags or []

		flags.append('--bind')
		return FileSystemManager.mount(source, target, flags, mount_options)

	@staticmethod
	def build_mount_options_string(options_list):
		if not options_list:
			return

	@staticmethod
	def umount(target):
		cmd = 'umount {target}'.format(target=target)

		exit_code, stdout, stderr = Utils.run_command(cmd)
		logger.debug("umount finished {} {} {}".format(exit_code, stdout, stderr))

		if exit_code != 0:
			if 'not mounted' in stderr:
				# this is not an error
				return
			elif 'target is busy' in stderr:
				raise MountTargetIsBusyError(stderr)
			else:
				raise Exception("umount failed exit_code={} stdout={} stderr={}".format(exit_code, stdout, stderr))

	@staticmethod
	def mkfs(fs_type, target_path, flags=None):
		if not fs_type:
			raise ArgumentError("fs_type argument Cannot be None or an empty string")

		if not flags:
			flags = []

		cmd = "mkfs.{fs_type} {flags} {target_path}".format(fs_type=fs_type, flags=' '.join(flags), target_path=target_path)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise OSError("mkfs failed {} {} {}".format(exit_code, stdout, stderr))

	@staticmethod
	def get_fs_type(target_path):
		cmd = "blkid {} | awk '{{ print $3}}' | cut -c 7- | rev | cut -c 2- | rev".format(target_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return stdout.strip()

	@staticmethod
	def remove_dir(dir_path):
		return shutil.rmtree(dir_path)

	@staticmethod
	def format_block_device(block_device_path, fs_type):
		# check if already formatted, and if format meets request
		current_fs_type = FileSystemManager.get_fs_type(block_device_path)
		logger.debug('current_fs_type={}'.format(current_fs_type))
		if current_fs_type == fs_type:
			logger.debug('{} is already formatted to {}'.format(block_device_path, current_fs_type))
			return

		if current_fs_type != '':
			raise DriverError(StatusCode.INVALID_ARGUMENT, '{} is formatted to {} but requested {}'.format(block_device_path, current_fs_type, fs_type))

		FileSystemManager.mkfs(fs_type=fs_type, target_path=block_device_path, flags=[])

	@staticmethod
	def expand_file_system(block_device_path, fs_type):
		fs_type = fs_type.strip()

		if fs_type == 'devtmpfs':
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Device not formatted with FileSystem found fs type {}'.format(fs_type))
		elif fs_type.startswith('ext'):
			cmd = 'resize2fs {}'.format(block_device_path)
		elif fs_type == Consts.FSType.XFS:
			cmd = 'xfs_growfs {}'.format(block_device_path)
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'unknown fs_type {}'.format(fs_type))

		exit_code, stdout, stderr = Utils.run_command(cmd)
		logger.debug("resize file-system finished {} {} {}".format(exit_code, stdout, stderr))

		if exit_code != 0:
			raise DriverError(StatusCode.INTERNAL, 'Error expanding File System {} on block device {}'.format(fs_type, block_device_path))

		return exit_code, stdout, stderr

	@staticmethod
	def get_file_system_type(target_path):
		cmd = "df -T {} | tail -1 | awk '{{ print $2}}'".format(target_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return stdout

	@staticmethod
	def get_block_device_size(block_device_path):
		cmd = "lsblk {} --output SIZE | tail -1".format(block_device_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return stdout.strip()