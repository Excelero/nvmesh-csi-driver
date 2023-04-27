import unittest

from driver.version_compatibility import SemVerConstraintList, CompatibilityValidator, VersionMatrix
from driver.semver import SemVer

class TestVersionCompatibility(unittest.TestCase):
    def test_semver_parser(self):
        self.assertTrue(SemVer.parse('1.2.7') < SemVer.parse('1.3.0'))
        self.assertTrue(SemVer.parse('1.3.0') == SemVer.parse('1.3.0'))
        self.assertTrue(SemVer.parse('1.3.0') >= SemVer.parse('1.3.0'))
        self.assertTrue(SemVer.parse('1.3.0') >= SemVer.parse('1.2.7'))

        self.assertFalse(SemVer.parse('1.2.7-1') == SemVer.parse('1.3.0-42'))
        self.assertFalse(SemVer.parse('1.2.7-23') > SemVer.parse('1.3.0-23'))
        self.assertFalse(SemVer.parse('1.2.7') >= SemVer.parse('1.3.0'))

    def test_semver_parser_release_and_arch(self):
        self.assertTrue(SemVer.parse('2.7.0-23') == SemVer.parse('2.7.0-56-ubuntu_x64'))

    def test_constraint_validator(self):
        self.assertTrue(SemVerConstraintList('<1.3.0 >=1.2.7').is_valid(SemVer.parse('1.2.8')))
        self.assertTrue(SemVerConstraintList('<1.3.0 >=1.2.7').is_valid(SemVer.parse('1.2.7')))

        self.assertFalse(SemVerConstraintList('<1.3.0 >=1.2.7').is_valid(SemVer.parse('1.3.0')))
        self.assertFalse(SemVerConstraintList('<1.3.0 >=1.2.7').is_valid(SemVer.parse('1.4.0')))
        self.assertFalse(SemVerConstraintList('<1.3.0 >=1.2.7').is_valid(SemVer.parse('1.2.6')))

    def test_compatibility_matrix_valid(self):
        mock_version_matrix = {
            '>=1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.6.0 <2.8.0'
            },
            '>=1.2.0 <1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.2.0 <2.6.0'
            }
        }

        mat = VersionMatrix(mock_version_matrix)

        validator = CompatibilityValidator(mat)
        validator.csi_version = SemVer.parse('1.3.0')

        validator.validate_nvmesh_core(SemVer.parse('2.7.0'))
        validator.validate_nvmesh_mgmt(SemVer.parse('2.7.0'))
        validator.validate_k8s(SemVer.parse('1.22.5'))


    def test_compatibility_matrix_invalid(self):
        mock_version_matrix = {

            '>=1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.6.0 <2.8.0'
            },
            '>=1.2.0 <1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.5.0 <2.6.0'
            }
        }

        mat = VersionMatrix(mock_version_matrix)

        validator = CompatibilityValidator(mat)
        validator.csi_version = SemVer.parse('1.2.4-8')

        # This does not meet requirements

        with self.assertRaises(ValueError):
            validator.validate_k8s(SemVer.parse('1.25.1'))

        with self.assertRaises(ValueError):
            validator.validate_nvmesh_core(SemVer.parse('2.6.5'))

        with self.assertRaises(ValueError):
            validator.validate_nvmesh_mgmt(SemVer.parse('2.1.0'))

    def test_compatibility_matrix_csi_future_ver(self):
        mock_version_matrix = {
            '>=1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.6.0 <2.8.0'
            },
            '>=1.2.0 <1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.5.0 <2.6.0'
            }
        }

        mat = VersionMatrix(mock_version_matrix)
        validator = CompatibilityValidator(mat)
        validator.csi_version = SemVer.parse('1.4.0')

        validator.validate_k8s(SemVer.parse('1.24.1'))
        validator.validate_nvmesh_core(SemVer.parse('2.6.5-124-ubuntu'))
        validator.validate_nvmesh_mgmt(SemVer.parse('2.6.5-56'))

    def test_compatibility_matrix_csi_ver_not_found(self):
        mock_version_matrix = {
            '=1.3.0': {
                'kubernetes': '>=1.17.0 <1.25.0',
                'nvmesh': '>=2.6.0 <2.8.0'
            }
        }

        mat = VersionMatrix(mock_version_matrix)

        validator = CompatibilityValidator(mat)
        # checker.collect_versions()
        validator.csi_version = SemVer.parse('1.4.0')

        with self.assertRaises(ValueError):
            validator.validate_k8s(SemVer.parse('1.24.0'))