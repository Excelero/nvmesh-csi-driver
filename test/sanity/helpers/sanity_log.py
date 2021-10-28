import logging
import sys

LOG_LEVEL_QUIET = 0
LOG_LEVEL_DEFAULT = 1
LOG_LEVEL_VERBOSE = 2
LOG_LEVEL_DEBUG = 3

def print_all_configured_loggers():
	loggers = [name for name in logging.root.manager.loggerDict]
	print(loggers)

def add_stdout_logger(logger):
	handler = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
	handler.setFormatter(formatter)
	logger.addHandler(handler)

def setup_logging_level():
	from test.sanity.helpers.sanity_test_config import SanityTestConfig
	level = SanityTestConfig.LogLevel

	sanity_logger = logging.getLogger('SanityTests')
	if not len(sanity_logger.handlers):
		add_stdout_logger(sanity_logger)

	root_logger = logging.getLogger()
	driver_logger = logging.getLogger('CSIDriver')
	sdk_logger = logging.getLogger('NVMeshSDK')
	mgmt_ws_client = logging.getLogger('mgmt-ws-client')
	urllib3_logger = logging.getLogger('urllib3.connectionpool')
	topology_logger = logging.getLogger('topology')
	topology_svc_logger = logging.getLogger('topology-service')

	all_loggers = [
		sdk_logger,
		driver_logger,
		sanity_logger,
		mgmt_ws_client,
		urllib3_logger,
		topology_logger,
		topology_svc_logger,
	]

	# By default turn all loggers off
	for l in all_loggers + [root_logger]:
		l.removeHandler(sys.stderr)
		l.removeHandler(sys.stdout)

	if level == LOG_LEVEL_QUIET:
		# Should preferably output nothing
		pass

	if level == LOG_LEVEL_DEFAULT:
		# Should print only Unittest output
		for l in all_loggers:
			l.setLevel(logging.CRITICAL)

		sanity_logger.setLevel(logging.ERROR)

	if level >= LOG_LEVEL_VERBOSE:
		# Should print Unittest with some general flow test prints
		sanity_logger.setLevel(logging.INFO)
		root_logger.setLevel(logging.WARNING)

	if level >= LOG_LEVEL_DEBUG:
		# Maximum amount of logs
		for l in all_loggers:
			l.setLevel(logging.DEBUG)

		if not len(root_logger.handlers):
			add_stdout_logger(root_logger)
