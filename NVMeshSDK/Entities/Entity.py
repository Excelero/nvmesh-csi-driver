#!/usr/bin/env python
from NVMeshSDK.Utils import Utils

import json
import copy


class Entity(object):

    def __str__(self):
        dictCopy = copy.deepcopy(self.__dict__)
        try:
            del dictCopy['_{0}__objectsToInstantiate'.format(self.__class__.__name__)]
        except KeyError:
            pass
        return json.dumps(dictCopy, sort_keys=True, indent=4, default=lambda x: x.__dict__)

    def __getattribute__(self, item):
        if '.' in item:
            parts = item.split('.')
            field = Entity.__getattribute__(self, parts[0])
            if isinstance(field, list):
                array = field
                return [getattr(a, parts[1]) for a in array]
            else:
                return getattr(field, parts[1])
        else:
            return object.__getattribute__(self, item)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            selfDict = Entity.myToDict(self)
            otherDict = Entity.myToDict(other)
            return selfDict == otherDict

        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self._id < other._id

        return False

    @staticmethod
    def myToDict(obj):
        return json.loads(json.dumps(obj.__dict__ if not isinstance(obj, dict) else obj, default=lambda x: x.__dict__))

    def serialize(self):
        return Entity.myToDict(self.filterNoneValues())

    def deserialize(self):
        self.instantiate()

    def instantiate(self):
        for obj in self.getObjectsToInstantiate():
            entityRep = getattr(self, obj)
            if hasattr(self, entityRep.dbKey):
                attrValue = getattr(self, entityRep.dbKey)
                if isinstance(attrValue, list):
                    listOfInstances = []
                    for element in attrValue:
                        element = entityRep.type(**element)
                        listOfInstances.append(element.instantiate() if element.getObjectsToInstantiate() != [] else element)

                    setattr(self, entityRep.dbKey, listOfInstances)
                else:
                    setattr(self, entityRep.dbKey, entityRep.type(**attrValue))
        return self

    def filterNoneValues(self):
        return {k: v for k, v in self.__dict__.iteritems() if v is not None}

    def getObjectsToInstantiate(self):
        return []

    def isValid(self):
        status = {'valid': None, 'error': None}

        if not self.__writeEntityToFile():
            status['error'] = 'Unable to write the entity to a file'
        else:
            cmd = [
                'node',
                '/opt/NVMesh/management/validator.js',
                self.pathToSerializedEntityFile,
                self.getSchemaName()
            ]
            stdout, err = Utils.executeLocalCommand(cmd)
            if err:
                status['error'] = err
            else:
                status = json.loads(stdout)

        delattr(self, 'pathToSerializedEntityFile')

        status['id'] = getattr(self, self.Id.dbKey)
        status['type'] = self.getSchemaName()
        return status

    def __writeEntityToFile(self):
        success = True
        serializedEntitiesPath = '/opt/NVMesh/cli/NVMeshSDK/Tests/serializedEntities'

        Utils.createDirIfNotExists(path=serializedEntitiesPath)

        self.pathToSerializedEntityFile = '{0}/{1}_{2}.json'.format(serializedEntitiesPath, self.getSchemaName(), getattr(self, self.Id.dbKey))

        try:
            with open(self.pathToSerializedEntityFile, 'w+') as f:
                json.dump(Entity.myToDict(self), f)

        except EnvironmentError as e:
            success = False

        return success

    @staticmethod
    def getSchemaName():
        pass
