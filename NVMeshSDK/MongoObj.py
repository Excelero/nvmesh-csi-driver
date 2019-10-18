from NVMeshSDK.Entities.AttributeRepresentation import AttributeRepresentation


class MongoObj(object):
    def __init__(self, field, value):
        """**Represents a mongoDB query object**

        :param field: entity attribute
        :type field: str
        :param value: mongoDB query value
        :type value: int or str
        """
        self.value = value

        if isinstance(field, list):
            self.field = self.__getNestedFieldsStr(fields=[f.dbKey if isinstance(f, AttributeRepresentation) else f for f in field])
        else:
            self.field = field.dbKey if isinstance(field, AttributeRepresentation) else field

    def __getNestedFieldsStr(self, fields):
        return '.'.join(fields)

