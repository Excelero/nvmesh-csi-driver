#!/usr/bin/env python

from functools import wraps
import inspect
import json
import subprocess
import os
import re


class Utils:

    @staticmethod
    def initializer(func):
        argSpec = inspect.getargspec(func)
        names, varargs, keywords, defaults = argSpec

        @wraps(func)
        def wrapper(self, *args, **kargs):
            for name, arg in list(zip(names[1:], args)) + list(kargs.items()):
                setattr(self, name, arg)

            for name, default in zip(reversed(names), reversed(defaults)):
                if not hasattr(self, name):
                    if default is not None:
                        setattr(self, name, default)

            filteredKargs = {k: v for k, v in kargs.iteritems() if k in names}
            func(self, *args, **filteredKargs)

        wrapper.argSpec = argSpec

        return wrapper

    @staticmethod
    def createMongoQueryObj(mongoObects):
        return {mongoObj.field: mongoObj.value for mongoObj in mongoObects}

    @staticmethod
    def buildQueryStr(queryParams):
        query = '?'
        isFirstParam = True

        for paramName, paramValue in queryParams.iteritems():
            if paramValue is not None:
                if not isFirstParam:
                    query += '&'
                else:
                    isFirstParam = False

                query += '{0}={1}'.format(paramName, json.dumps(Utils.createMongoQueryObj(paramValue)))

        if len(query) == 1:
            query = ''

        return query

    @staticmethod
    def convertUnitCapacityToBytes(unitCapacity):
        def getMultipleOfBytesType(unitCapacity):
            binary = 1024
            decimal = 1000
            return binary if 'i' in unitCapacity else decimal

        def getFactor(termFirstLetter):
            return {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5}[termFirstLetter]

        if type(unitCapacity) not in (unicode, str) or unitCapacity.lower() == 'max':
            return unitCapacity

        unitCapacity = unitCapacity.lower()
        multipleOfBytesType = getMultipleOfBytesType(unitCapacity)

        search = re.search(r"([0-9]*\.?[0-9]+)(\w+)", unitCapacity)
        value = search.group(1)
        term = search.group(2)
        factor = getFactor(term[:1])

        return float(value) * multipleOfBytesType ** factor

    @staticmethod
    def convertBytesToUnit(bytes):
        def getUnitType(multiplier):
            if multiplier == 1:
                unitType = 'KiB'
            elif multiplier == 2:
                unitType = 'MiB'
            elif multiplier == 3:
                unitType = 'GiB'
            else:
                unitType = 'TiB'

            return unitType

        if not isinstance(bytes, (int, long, float)):
            return bytes

        counter = 0
        someUnits = bytes

        while someUnits / 1000 >= 1:
            counter += 1
            someUnits /= 1000

        if counter == 0:
            return str(bytes) + 'B'
        else:
            division = float(bytes) / float(1024 ** counter)

            return str(round(((division * 100) / 100), 2)) + getUnitType(counter)

    @staticmethod
    def executeLocalCommand(command):
        try:
            out = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = out.communicate()
            return stdout, stderr
        except OSError as e:
            return None, e

    @staticmethod
    def readConfFile(confFile):
        g = {}
        l = {}

        try:
            if not os.path.exists(confFile):
                return False
            else:
                execfile(confFile, g, l)
                return l
        except Exception:
            return False


    @staticmethod
    def createDirIfNotExists(path):
        if not os.path.exists(path):
            os.makedirs(path)