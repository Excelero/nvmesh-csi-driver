#!/usr/bin/env python
from NVMeshSDK.Utils import Utils
from NVMeshSDK.Entities.Entity import Entity
from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class ConfigurationProfile(Entity):
	"""
	Static class attributes to use with MongoObj
			* Id
			* Description
			* Labels
			* Hosts
			* Configuration
			* DateModified
			* ModifiedBy
	"""
	Id = AttributeRepresentation(display='Name', dbKey='_id')
	Description = AttributeRepresentation(display='Description', dbKey='description')
	Labels = AttributeRepresentation(display='Labels', dbKey='labels')
	Hosts = AttributeRepresentation(display='Hosts', dbKey='hosts')
	Configuration = AttributeRepresentation(display='Configuration', dbKey='config')
	DateModified = AttributeRepresentation(display='Date Modified', dbKey='dateModified')
	ModifiedBy = AttributeRepresentation(display='Modified By', dbKey='modifiedBy')

	@Utils.initializer
	def __init__(self, name, _id=None, description=None, labels=None, hosts=None, config=None, version=None, modifiedBy=None, createdBy=None, dateModified=None, dateCreated=None, deleteNotAllowed=None, editNotAllowed=None):
		"""**Initializes configuration profile entity**

		:param _id: the id of the configuration profile
		:type _id: str
		:param name: the name of the configuration profile
		:type name: str
		:param description: description of the configuration profile, defaults to None
		:type description: str, optional
		:param labels: list of labels of the configuration profile
		:type labels: list, optional
		:param config: a dictionary of the configuration parameters and their values
		:type config: dict, optional
		:param modifiedBy: the last user that modified the configuration profile, defaults to None
		:type modifiedBy: str, optional
		:param dateModified: date of last modification, defaults to None
		:type dateModified: str, optional
		"""
		pass

	def getObjectsToInstantiate(self):
		return []

	@staticmethod
	def getSchemaName():
		return 'configurationProfileEntity'