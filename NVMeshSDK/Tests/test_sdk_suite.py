import unittest

from NVMeshSDK.Tests.TestUser import UserTest
from NVMeshSDK.Tests.TestVPG import VPGTest
from NVMeshSDK.Tests.TestVolume import VolumeTest
from NVMeshSDK.Tests.TestTargetClass import TargetClassTest
from NVMeshSDK.Tests.TestLog import LogTest
from NVMeshSDK.Tests.TestTarget import TargetTest
from NVMeshSDK.Tests.TestDriveClass import DriveClassTest
from NVMeshSDK.Tests.TestDrive import DriveTest
from NVMeshSDK.Tests.TestClient import ClientTest


def getTestSuite():
    """
       Gather all the tests from this module in a test suite.
    """
    test_suite = unittest.TestSuite()
    tests_list = [
        UserTest, TargetTest, ClientTest, DriveTest, DriveClassTest,
        LogTest, TargetClassTest, VolumeTest, VPGTest
    ]

    for test in tests_list:
        test_suite.addTest(unittest.makeSuite(test))

    return test_suite


if __name__ == "__main__":
    mySuit = getTestSuite()
    runner = unittest.TextTestRunner()
    runner.run(mySuit)
