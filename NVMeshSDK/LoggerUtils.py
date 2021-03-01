import logging
import os
import sys
import traceback

from logging.handlers import SysLogHandler
from NVMeshSDK import Consts


class Logger(object):
	def __init__(self, mainLoggerName='NVMeshSDK'):
		self._mainLoggerName = mainLoggerName
		self._mainLogger = logging.getLogger(mainLoggerName)
		self._defaultFormat = '%(name)s[{}]: %(levelname)s: %(message)s'.format(os.getpid())
		self._isLoggerInitialized = False
		self._loggerOptions = {
			'logToSysLog': True,
			'logToStdout': False,
			'logToStderr': False,
			'logLevel': logging.DEBUG,
			'propagate': True,
			'formatString': self._defaultFormat,
			'sysLogAddress': Consts.SYSLOG_PATH
		}

	def getLogger(self, loggerName):
		if not self._isLoggerInitialized:
			self._configLogger(**self._loggerOptions)
			self._isLoggerInitialized = True

		return self._mainLogger.getChild(loggerName)

	def getOptions(self):
		return self._loggerOptions

	def setOptions(self, **kwargs):
		self._loggerOptions.update(kwargs)

	def _configLogger(self, logToSysLog=None, logToStdout=None, logToStderr=None, logLevel=None, propagate=None, formatString=None, sysLogAddress=None):
		if propagate is not None:
			self._mainLogger.propagate = propagate

		if logLevel is not None:
			self._mainLogger.setLevel(logLevel)

		_logging_formatter = logging.Formatter(formatString) if formatString else None

		if logToSysLog:
			_syslogHandler = SysLogHandler(address=sysLogAddress)
			_syslogHandler.setFormatter(_logging_formatter)
			_syslogHandler.setLevel(logLevel)
			self._mainLogger.addHandler(_syslogHandler)

		if logToStdout:
			_stdoutHandler = logging.StreamHandler(sys.stdout)
			_stdoutHandler.setFormatter(_logging_formatter)
			_stdoutHandler.setLevel(logLevel)
			self._mainLogger.addHandler(_stdoutHandler)

		if logToStderr:
			_stderrHandler = logging.StreamHandler(sys.stderr)
			_stderrHandler.setFormatter(_logging_formatter)
			_stderrHandler.setLevel(logLevel)
			self._mainLogger.addHandler(_stderrHandler)


def logStackTrace(ex, logger):
	exc_type, exc_value, exc_traceback = sys.exc_info()
	exString = traceback.format_exc()
	errorLines = exString.split('\n')

	for line in errorLines:
		logger.error(line)