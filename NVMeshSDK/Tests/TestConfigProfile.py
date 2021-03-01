import unittest

from NVMeshSDK.MongoObj import MongoObj

import TestBaseClass

from NVMeshSDK.APIs.ConfigurationProfileAPI import ConfigurationProfileAPI
from NVMeshSDK.Entities.ConfigurationProfile import ConfigurationProfile

class ConfigurationProfileTest(TestBaseClass.TestBaseClass):
	NUMBER_OF_EXPECTED_PROFILES = 3

	def getDbEntities(self):
		return [
			ConfigurationProfile(name="NVMesh Default",
								 _id="NVMesh Default",
								 labels=[],
								 hosts=[],
								 config= {
					"MLX5_RDDA_ENABLED": True,
					"IPV4_ONLY": True,
					"DUMP_FTRACE_ON_OOPS": False,
					"MANAGEMENT_PROTOCOL": "https",
					"MCS_LOGGING_LEVEL": "INFO",
					"AGENT_LOGGING_LEVEL": "INFO",
					"AUTO_ATTACH_VOLUMES": True
				},
								 modifiedBy=u"admin@excelero.com",
								 createdBy=u"admin@excelero.com",
								 dateModified=u"2019-10-30T14:08:36.777Z",
								 dateCreated=u"2019-10-30T14:08:36.777Z",
								 deleteNotAllowed=True,
								 editNotAllowed=True,
								 version=1,
								 uuid="nvmesh_default"
								 ),
			ConfigurationProfile(name="NVMesh Debug",
								 _id="NVMesh Debug",
								 labels=[],
								 hosts=[],
								 config={
				  "TOMA_BUILD_TYPE": "Verbose",
				  "DUMP_FTRACE_ON_OOPS": True,
				  "MCS_LOGGING_LEVEL": "DEBUG",
				  "AGENT_LOGGING_LEVEL": "DEBUG",
				},
								 modifiedBy=u"admin@excelero.com",
								 createdBy=u"admin@excelero.com",
								 dateModified=u"2019-10-30T14:08:36.778Z",
								 dateCreated=u"2019-10-30T14:08:36.778Z",
								 deleteNotAllowed=True,
								 editNotAllowed=False,
								 version=1,
								 uuid="nvmesh_debug"
								 ),
				ConfigurationProfile(name="Cluster Default",
									 _id="Cluster Default",
									 labels=[],
									 hosts=[],
									 config={
							"MLX5_RDDA_ENABLED" : True,
							"IPV4_ONLY" : True,
							"DUMP_FTRACE_ON_OOPS" : False,
							"MANAGEMENT_PROTOCOL" : "https",
							"MCS_LOGGING_LEVEL" : "INFO",
							"AGENT_LOGGING_LEVEL" : "INFO",
							"AUTO_ATTACH_VOLUMES" : True
						},
									 modifiedBy=u"admin@excelero.com",
									 createdBy=u"admin@excelero.com",
									 dateModified=u"2019-10-30T14:08:36.777Z",
									 dateCreated=u"2019-10-30T14:08:36.777Z",
									 deleteNotAllowed=True,
									 editNotAllowed=False,
									 version=1,
									 uuid="cluster_default"
									 ),
		]

	def getApiUpdatePayload(self):
		profiles = self.getDbEntities()
		for p in profiles:
			p.hosts = ['server1']
		return profiles

	def testZ_01_load_defaults(self):
		profiles = self.getDbEntities()
		err, apiRes = self.myAPI.save(profiles)
		self.assertIsNone(err)

	def testZ_02_count(self):
		err, apiRes = self.myAPI.count()
		self.checkResults(self.NUMBER_OF_EXPECTED_PROFILES, err, apiRes, apiAssert=self.assertEqual)

	def testZ_03_save_custom_profile(self):
		config = {
				"MLX5_RDDA_ENABLED": True,
				"IPV4_ONLY": True,
				"DUMP_FTRACE_ON_OOPS": False,
				"MANAGEMENT_PROTOCOL": "https",
				"MANAGEMENT_SERVERS": ["mgmt1:40001","mgmt2:4001"],
				"CONFIGURED_NICS": ["ib0","ib1"],
				"MCS_LOGGING_LEVEL": "INFO",
				"AGENT_LOGGING_LEVEL": "INFO",
				"AUTO_ATTACH_VOLUMES": True
			}

		newProfile = ConfigurationProfile(
			name="Test New Profile",
			description="This profile is used for testing the SDK Api",
			labels=["SDK","tests"],
			config=config
		)

		err, apiRes = self.myAPI.save([newProfile])

	def testZ_04_apply_to_hosts(self):

		newProfile = ConfigurationProfile(
			name="Test New Profile",
			hosts=[],
			description="new description !!!",
			labels=["updated"],
			version=3
		)

		err, apiRes = self.myAPI.save([newProfile])
		self.assertIsNone(err)

		newProfile.hosts = ["scale-{}.excelero.com".format(i) for i in range(1, 10)]
		err, apiRes = self.myAPI.update([newProfile])
		self.assertIsNone(err)
		self.assertTrue(apiRes[0]['success'])

		err, apiRes = self.myAPI.get(filter=[MongoObj(field='_id', value='Test New Profile')])
		self.assertIsNone(err)
		self.assertListEqual(apiRes[0].hosts, newProfile.hosts)

	def testZ_05_delete(self):
		newProfile = ConfigurationProfile(name="Test New Profile")
		expectedRes = self.getExpectedResultObj(entities=[newProfile], idAttr='name')
		err, apiRes = self.myAPI.delete([newProfile])
		self.checkResults(expectedRes, err, apiRes)

	def testZ_05_delete_profile_not_found_should_fail(self):
		newProfile = ConfigurationProfile(name="Not FoundProfile")
		err, apiRes = self.myAPI.delete([newProfile])
		self.assertFalse(apiRes[0]['success'])
		self.assertTrue('Configuration Profile not found' in apiRes[0]['error'])

	def testZ_06_update_profile(self):
		profile = ConfigurationProfile("Cluster Default", uuid="cluster_default", hosts=[], config={})
		err, res = ConfigurationProfileAPI().update([profile])

		# should succeed
		self.assertTrue(res[0]['success'])

	def testZ_05_update_profile_not_found_should_fail(self):
		newProfile = ConfigurationProfile(name="Not FoundProfile", hosts=['hey', 'yo'])
		err, apiRes = self.myAPI.update([newProfile])
		self.assertFalse(apiRes[0]['success'])
		self.assertTrue('Configuration Profile not found' in apiRes[0]['error'])

	def testZ_07_update_non_editable_should_fail(self):
		profile = ConfigurationProfile("NVMesh Default", uuid="nvmesh_default", hosts=[], config={})
		err, res = ConfigurationProfileAPI().update([profile])
		# Should Fail
		self.assertFalse(res[0]['success'])

	@unittest.skipIf(True, 'Not Implemented')
	def testDelete(self):
		pass

	@unittest.skipIf(True, 'Not Implemented')
	def testSave(self):
		pass

	@staticmethod
	def getAPI():
		return ConfigurationProfileAPI()

	@staticmethod
	def test999():
		return ConfigurationProfileAPI()


if __name__ == '__main__':
	unittest.main(verbosity=2)
