import os

import shutil

from driver.common import Utils, DriverLogger

logger = DriverLogger("FileSystemManager")

class ArgumentError(Exception):
	pass

class MountError(Exception):
	pass

class MountTargetIsBusyError(MountError):
	pass

class FileSystemManager(object):

	@staticmethod
	def create_fake_nvmesh_block_device(block_device_path):
		# Creates a Fake block device
		# This function is used for development, for testing with kubernetes on Host that are unable to actually install NVMesh Core Modules
		# TODO: remove when not needed

		cmd = 'mkdir -p /dev/nvmesh/'
		Utils.run_command(cmd)

		cmd = 'dd if=/dev/zero of={} bs=1M count=256'.format(block_device_path)
		Utils.run_command(cmd)

	@staticmethod
	def is_mounted(mount_path):
		cmd = 'grep -qs "{} " /proc/mounts'.format(mount_path)
		exit_code, stdout, stderr = Utils.run_command(cmd)
		return exit_code == 0

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
