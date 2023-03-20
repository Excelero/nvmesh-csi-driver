import logging
import os.path

from common import Utils
from subprocess import Popen, PIPE

logger = logging.getLogger("DMCrypt")

#NOTE: 
# when using run_command make sure debug is false so we don't print out the security key to the logs

class ShellCommandError(Exception):
    def __init__(self, message, cmd, exit_code, stderr, stdout):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.error_message = message
        message = '{} cmd="{}" exit_code={} stderr={} stdout={}'.format(
                message, cmd, exit_code, stderr, stdout)
        Exception.__init__(self, message)

class DMCrypt(object):
    WRONG_KEY = 2
    DEVICE_NOT_ENCRYPTED = 1
    ACCESS_DENIED_OR_NOT_EXIST = 4
    ALREADY_EXISTS = 5

    @staticmethod
    def get_mapped_device_path(nvmesh_volume_name):
        return '/dev/mapper/{}'.format(nvmesh_volume_name)

    @staticmethod
    def is_device_encrypted(dev_path, key):
        # checks if the device is formatted as LUKS
        # return codes: 
        # 0 - encrpyted and the given key is correct
        # 1 - device not encrypted
        # 2 - already encrypted wrong key given
        # 4 - access denied or device does not exist
        cmd = ['cryptsetup', 'open', '--test-passphrase', dev_path]
        logger.debug('checking for LUKS header: ' + ' '.join(cmd))
        exit_code, stdout, stderr = Utils.run_safe_command(cmd, input=key, debug=False)
        if exit_code == 0:
            return True, None
        elif exit_code == 1:
            return False, None
        else:
            err = ShellCommandError('got unexpected exit code from cryptsetup open', cmd, exit_code, stderr, stdout)
            return None, err

    @staticmethod
    def is_open(dev_name):
        map_path = DMCrypt.get_mapped_device_path(dev_name)
        return os.path.exists(map_path)

    @staticmethod   
    def luksFormat(dev_path, key, flags):
        # creates a Luks header on a device that was not encrypted before
        # this command ingores any previous headers
        cmd = ['cryptsetup','-q', 'luksFormat']
        for flag, value in flags.iteritems():
            cmd.append(flag)
            cmd.append(value)

        cmd.append(dev_path)

        logger.debug('running cmd: ' + ' '.join(cmd))
        exit_code, stdout, stderr = Utils.run_safe_command(cmd, input=key, debug=False)
        if exit_code == 0:
            return None
        elif exit_code == 2:
            return DMCrypt.WRONG_KEY
        else:
            return ShellCommandError('Error encrypting device ', cmd, exit_code, stderr, stdout)
    
    @staticmethod
    def open(dev_path, new_dev_name, key):
        # create a new device under /dev/mapper/{new_dev_name} 
        # and every IO command to this device will go through the dmCrypt layer 
        # before continuing to the underlying nvmesh device
        cmd = ['cryptsetup', 'open', dev_path, new_dev_name]
        logger.debug('running cmd: {}'.format(' '.join(cmd)))
        exit_code, stdout, stderr = Utils.run_safe_command(cmd, input=key, debug=False)
        if exit_code != 0:
            return ShellCommandError('Error opening encrypted device', cmd, exit_code, stderr, stdout)
        else:
            return None
    
    @staticmethod
    def close(encrypted_dev_name):
        # close an encrypted device (dev/mapper/{encrypted_dev_name})
        # this will remove the mapping to /dev/mapper
        cmd = ['cryptsetup','close', encrypted_dev_name]
        logger.debug('closing encrypted device ' + encrypted_dev_name)
        exit_code, stdout, stderr = Utils.run_safe_command(cmd, debug=True)
        if exit_code != 0:
            return ShellCommandError('Error closing encrypted device', cmd, exit_code, stderr, stdout)
        else:
            return None
