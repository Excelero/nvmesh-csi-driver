import logging
import json

from config import Config
from common import Utils
from sdk_helper import NVMeshSDKHelper
import config_map_api
import consts
from semver import SemVerConstraintList, SemVer

logger = logging.getLogger('VersionChecker')


class VersionMatrix(object):
	def __init__(self, csi_versions=None):
		self.matrix = csi_versions or {}

	def load_from_config_map(self):
		config_map_api.init()
		config_map = config_map_api.load(consts.VERSION_MATRIX_CONFIGMAP_NAME)
		comp_matrix = config_map.data.get('comp_matrix')
		self.matrix = json.loads(comp_matrix)

	def get_constraints_for_csi_version(self, csi_version):
		for csi_v_range, entry in self.matrix.iteritems():
			constraint_validator = SemVerConstraintList(csi_v_range)
			if constraint_validator.is_valid(csi_version):
				# Found the relevant entry in the matrix for this CSI version
				return entry

		# if we got here it means we couldn't find a matching rule for this CSI Version
		raise ValueError('Could not find compatibility info for CSI Driver version {}. compatibility matrix: {}'.format(csi_version, self))

	def __str__(self):
		return '\n' + json.dumps(self.matrix, indent=4)

class CompatibilityValidator(object):
	def __init__(self, comp_matrix):
		self.comp_matrix = comp_matrix
		self.csi_version = Config.DRIVER_VERSION

	def fetch_and_validate_nvmesh_mgmt_version(self, api):
		nvmesh_mgmt_version = VersionFetcher.get_management_version(api)
		self.validate_nvmesh_mgmt(nvmesh_mgmt_version)

	def validate_k8s(self, k8s_version):
		constraint_dict = self.comp_matrix.get_constraints_for_csi_version(self.csi_version)
		k8s_constraints = constraint_dict.get('kubernetes', None)
		if k8s_constraints:
			if not SemVerConstraintList(k8s_constraints).is_valid(k8s_version):
				raise ValueError('CSI Driver version {} requires Kubernetes version {} but found kubernetes {}. compatibility matrix: {}'.format(
					self.csi_version, k8s_constraints, k8s_version, self.comp_matrix))

	def validate_nvmesh_core(self, nvmesh_core_version):
		constraint_dict = self.comp_matrix.get_constraints_for_csi_version(self.csi_version)
		nvmesh_constraints = constraint_dict.get('nvmesh', None)
		if not SemVerConstraintList(nvmesh_constraints).is_valid(nvmesh_core_version):
			raise ValueError('CSI Driver version {} requires NVMesh version {} but found NVMesh {}. Compatibility matrix: {}'.format(
				self.csi_version, nvmesh_constraints, nvmesh_core_version, self.comp_matrix))

	def validate_nvmesh_mgmt(self, nvmesh_mgmt_version):
		constraint_dict = self.comp_matrix.get_constraints_for_csi_version(self.csi_version)
		nvmesh_constraints = constraint_dict.get('nvmesh', None)
		if not SemVerConstraintList(nvmesh_constraints).is_valid(nvmesh_mgmt_version):
			raise ValueError('CSI Driver version {} requires NVMesh version {} but found NVMesh Management {}. Compatibility matrix: {}'.format(
				self.csi_version, nvmesh_constraints, nvmesh_mgmt_version, self.comp_matrix))


class VersionFetcher(object):

	@staticmethod
	def get_nvmesh_core_version():
		cmd = 'cat /opt/NVMesh/client-repo/version'

		exit_code, stdout, stderr = Utils.run_command(cmd)
		if exit_code != 0:
			raise ValueError('Failed to get NVMesh Core version. exit_code: {} stdout: {} stderr: {}'.format(exit_code, stdout, stderr))

		# Example command output
		# $ cat /opt/NVMesh/client-repo/version
		# version="2.5.2-66.el7_9"
		# commit="3791ddb54"
		# branch="heads/2.5.2"

		try:
			first_line = stdout.split('\n')[0]
			version_string = first_line.split('=')[1][1:-1]
			legal_semver_str = '.'.join(version_string.split('.')[0:-1])
			sem_ver_obj = SemVer.parse(legal_semver_str)
		except Exception as ex:
			logger.error('Failed to parse nvmesh-core version command: {} output: {}'.format(cmd, stdout))
			raise ex

		return sem_ver_obj

	@staticmethod
	def get_management_version(api):
		management_version_info = NVMeshSDKHelper.get_management_version(api)
		return management_version_info.get('version')
