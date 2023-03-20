import logging
import shutil

from grpc import StatusCode

from common import Utils, DriverError
from consts import FSType

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
	def chmod(permissions_mask, path):
		cmd = 'chmod {mask} {path}'.format(mask=permissions_mask, path=path)
		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise Exception("Failed changing permissions on {} code:{} stdout:{} stderr:{}".format(path, exit_code, stdout, stderr))

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

		if fs_type == FSType.XFS:
			# support older host kernels which don't support this feature
			flags.append('-m reflink=0')

		cmd = "mkfs.{fs_type} {flags} {target_path}".format(fs_type=fs_type, flags=' '.join(flags), target_path=target_path)

		exit_code, stdout, stderr = Utils.run_command(cmd)

		if exit_code != 0:
			raise OSError("mkfs failed {} {} {}".format(exit_code, stdout, stderr))

	@staticmethod
	def get_fs_type(target_path):
		# returns an empty string for a block device that has no FileSystem on it
		# An alternate method is to use `df --output=fstype {target_path} | tail -1` but this will return "devtmpfs" if the block device has no FileSystem on it
		cmd = "blkid -o export {}".format(target_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		try:
			blkid_output = stdout.strip()
			if blkid_output == '':
				return blkid_output

			for line in blkid_output.split('\n'):
				key, value = line.split('=')
				if key == 'TYPE':
					return value.strip()

			raise ValueError('Could not find TYPE key in blkid output')
		except Exception as ex:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Could not determine file system type for path {}. Error: {}'.format(target_path, ex))

	@staticmethod
	def remove_dir(dir_path):
		return shutil.rmtree(dir_path)

	@staticmethod
	def format_block_device(block_device_path, fs_type, mkfs_options):
		# check if already formatted, and if format meets request
		current_fs_type = FileSystemManager.get_fs_type(block_device_path)
		logger.debug('current_fs_type={}'.format(current_fs_type))
		if current_fs_type == fs_type:
			logger.debug('{} is already formatted to {}'.format(block_device_path, current_fs_type))
			return

		if current_fs_type != '':
			raise DriverError(StatusCode.INVALID_ARGUMENT, '{} is formatted to {} but requested {}'.format(block_device_path, current_fs_type, fs_type))

		FileSystemManager.mkfs(fs_type=fs_type, target_path=block_device_path, flags=[mkfs_options])

	@staticmethod
	def expand_file_system(block_device_path, fs_type):

		if fs_type == '':
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'Device not formatted with FileSystem found fs type {}'.format(fs_type))
		elif fs_type == FSType.EXT4:
			cmd = 'resize2fs {}'.format(block_device_path)
		elif fs_type == FSType.XFS:
			cmd = 'xfs_growfs {}'.format(block_device_path)
		elif fs_type == FSType.CRYPTO_LUKS:
			cmd = 'cryptsetup resize {}'.format(block_device_path)
		else:
			raise DriverError(StatusCode.INVALID_ARGUMENT, 'unknown fs_type {}'.format(fs_type))

		exit_code, stdout, stderr = Utils.run_command(cmd)
		logger.debug("resize file-system finished exit_code: {}".format(exit_code))

		if exit_code != 0:
			raise DriverError(StatusCode.INTERNAL, 'Error expanding File System {} on block device {}'.format(fs_type, block_device_path))

		return exit_code, stdout, stderr

	@staticmethod
	def get_block_device_size_bytes(block_device_path):
		cmd = "lsblk --bytes --nodeps --output SIZE --noheadings %s" % block_device_path
		exit_code, stdout, stderr = Utils.run_command(cmd)
		size_in_bytes = int(stdout.strip())
		return size_in_bytes

	@staticmethod
	def get_file_system_size(mount_path):
		# Example output of df
		# Filesystem                          1K-blocks  	Used Avail Use% Mounted on
		# /dev/mapper/csi-b56c8a85-76cd-43d0  3119104   	33M  3.0G   2% /var/lib/ku..
		cmd = "df %s | awk '{ print $2 }' | tail -1" % mount_path
		exit_code, stdout, stderr = Utils.run_command(cmd)
		size_in_kb = stdout.strip()
		size_in_byte = int(size_in_kb) * 1024
		return size_in_byte
