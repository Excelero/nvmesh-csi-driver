import logging
import os
import sys
import traceback

from logging.handlers import SysLogHandler
import Consts

def getInfraClientLogger(loggername, logToSysLog=True, logToStdout=False, logToStderr=False, logLevel=logging.DEBUG,
						 formatString='%(name)s: %(levelname)s: %(message)s'):
	return getLoggerWithHandler('InfraClient.{0}[{1}]'.format(loggername,os.getpid()), logToSysLog, logToStdout, logToStderr, logLevel, formatString)

def getLoggerWithHandler(loggername, logToSysLog=True, logToStdout=False, logToStderr=False, logLevel=logging.DEBUG,
						 formatString='%(name)s: %(levelname)s: %(message)s'):
	logger = logging.getLogger(loggername)
	logger.propagate = False
	logger.setLevel(logLevel)
	loggingFormatter = logging.Formatter(formatString)

	logger.handlers = []

	if logToSysLog:
		sysLogHandler = SysLogHandler(address=Consts.SYSLOG_PATH)
		sysLogHandler.setFormatter(loggingFormatter)
		sysLogHandler.setLevel(logLevel)
		logger.addHandler(sysLogHandler)

	if logToStdout:
		stdoutHandler = logging.StreamHandler(sys.stdout)
		stdoutHandler.setFormatter(loggingFormatter)
		stdoutHandler.setLevel(logLevel)
		logger.addHandler(stdoutHandler)

	if logToStderr:
		stderrHandler = logging.StreamHandler(sys.stderr)
		stderrHandler.setFormatter(loggingFormatter)
		stderrHandler.setLevel(logging.ERROR)
		logger.addHandler(stderrHandler)

	return logger

def logStackTrace(ex, logger):
	exc_type, exc_value, exc_traceback = sys.exc_info()
	exString = traceback.format_exc()
	errorLines = exString.split('\n')
	
	for line in errorLines:
		logger.error(line)