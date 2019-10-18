from NVMeshSDK import LoggerUtils
from NVMeshSDK.Entities.Entity import Entity

import unittest
import subprocess
import pymongo
import json


class TestBaseClass(unittest.TestCase):
    COLLECTIONS_SET_UP = ['client', 'configurationVersion', 'diskClass', 'globalSettings', 'lastMessageLog', 'log',
                   'managementCluster', 'server', 'serverClass', 'server', 'volume', 'volumeProvisioningGroup', 'user']
    COLLECTIONS_TEAR_DOWN = ['client', 'diskClass', 'log', 'server', 'serverClass', 'server', 'volume', 'volumeProvisioningGroup', 'user']
    FIXTURES_PATH = '/'.join(['fixtures', 'management', '{0}.bson']) #'NVMeshSDK', 'Tests',

    @classmethod
    def setUpClass(cls):
        cls.className = cls.__name__
        cls.logger = LoggerUtils.getInfraClientLogger(cls.className)
        cls.myAPI = cls.getAPI()

        try:
            myClient = pymongo.MongoClient('mongodb://localhost:27017/')
            cls.logger.debug('Connected to mongoDB')
        except Exception as e:
            cls.logger.debug('Could not connect to mongoDB')
            raise e

        cls.db = myClient['management']

        for collection in cls.COLLECTIONS_SET_UP:
            command = ['mongorestore', '--db', 'management', cls.FIXTURES_PATH.format(collection)]
            try:
                cls.logger.debug('Loading collection: {0}'.format(collection))
                p = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                out, err = p.communicate()
                cls.logger.error(err)
                cls.logger.debug(out)
            except subprocess.CalledProcessError as e:
                cls.logger.debug('Unable to load {0} collection, error: {1}'.format(collection, e.message))

    @classmethod
    def tearDownClass(cls):
        for collection in cls.COLLECTIONS_TEAR_DOWN:
            result = cls.db[collection].remove()
            assert result['ok'] == 1.0

    def setUp(self):
        self.logger.debug('Running: {0}'.format(self._testMethodName))

    def tearDown(self):
        self.logger.debug('Tearing Down: {0}'.format(self._testMethodName))

    def test00Get(self):
        err, apiRes = self.myAPI.get()
        expectedRes = self.getDbEntities()
        self.checkResults(expectedRes, err, apiRes)

    def testSave(self):
        expectedRes = self.getExpectedResultObj(entities=self.getEntitiesForSave())
        err, apiRes = self.myAPI.save(self.getEntitiesForSave())
        self.checkResults(expectedRes, err,  apiRes)

    def testDelete(self):
        expectedRes = self.getExpectedResultObj(entities=self.getDbEntities())
        err, apiRes = self.myAPI.delete(self.getDbEntities())
        self.checkResults(expectedRes, err,  apiRes)

    def test10Update(self):
        expectedRes = self.getExpectedResultObj(entities=self.getDbEntities())
        err, apiRes = self.myAPI.update(self.getApiUpdatePayload())
        self.checkResults(expectedRes, err,  apiRes)

    def checkResults(self, expectedRes, err,  apiRes, errAssert=None, apiAssert=None):
        if errAssert is None:
            errAssert = self.assertIsNone
        if apiAssert is None:
            apiAssert = self.assertListEqual

        errAssert(err, 'Error from API in: {0}, test: {1}, err: {2}'.format(self.className, self._testMethodName, err))

        if isinstance(apiRes, list):
            apiRes.sort()
            expectedRes.sort()

        apiAssert(apiRes, expectedRes, self.__formatOutput(apiRes, expectedRes))

    def __formatOutput(self, apiRes, expectedRes):
        apiResStr = expectedResStr = ''

        if isinstance(apiRes, list):
            if isinstance(apiRes[0], Entity):
                for apiResult, expectedResult in list(zip(apiRes, expectedRes)):
                    apiResStr += apiResult.__str__() + '\n'
                    expectedResStr += expectedResult.__str__() + '\n'
            elif isinstance(apiRes[0], dict):
                apiResStr = json.dumps(apiRes, indent=4)
                expectedResStr = json.dumps(expectedRes, indent=4)
        else:
            apiResStr = apiRes
            expectedResStr = expectedRes

        return '\n\nFailed in: {0}, test: {1}\n\n=== API result:\n{2}\n=== Expected result:\n{3}\n'.format(
            self.className, self._testMethodName, apiResStr, expectedResStr)

    def getExpectedResultObj(self, entities, idAttr='_id', payload=None, success=True, error=None):
        return [self.getApiSuccessObj(_id=u'{0}'.format(getattr(obj, idAttr)), payload=payload, success=success, error=error)
                for obj in entities]

    def getApiSuccessObj(self, _id=None, payload=None, success=True, error=None):
        return {
            u"success": success,
            u"_id": _id,
            u"error": error,
            u"payload": payload
        }

    def getApiUpdatePayload(self):
        pass

    def getDbEntities(self):
        pass

    def getEntitiesForSave(self):
        pass

    @staticmethod
    def getAPI():
        pass