import argparse
import logging
import os
import signal
import sys
import subprocess
import yaml


log = logging.getLogger('nvmesh-csi-tester')
log.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(sys.stdout)
log.addHandler(stdout_handler)

namespace = None
default_mgmt_address = None


def read_value_from_file(filepath):
	try:
		with open(filepath, 'r') as file:
			data = file.read()
	except IOError as ex:
		return ''
	return data

def collect_info():
	global namespace
	namespace = read_value_from_file('/var/run/secrets/kubernetes.io/serviceaccount/namespace')

	global default_mgmt_address
	default_mgmt_address = 'nvmesh-management-0.nvmesh-management-ws.{namespace}.svc.cluster.local:4000'.format(namespace=namespace)

def get_available_tests(base_path):
	from os import walk

	module_names = []
	for (dirpath, dirnames, filenames) in walk(base_path):
		for filename in filenames:
			if filename.startswith('test_') and filename.endswith('.py'):
				module_name = filename[:-3]
				module_names.append(module_name)
		break

	return module_names

def print_available_tests(config):
	available_tests = get_available_tests(config['test_files_path'])
	print('Available Test Modules:')
	for mod in available_tests:
		print(mod)

def clear_environment():
	log.info('Clearing Environment')
	from test.integration.tests.utils import TestUtils
	TestUtils.clear_environment()

def run_test(config):
	if config['tests'] == 'all':
		cmd_arr = ['python2', '-m', 'unittest', 'discover', config['test_files_path']]
	else:
		test_list = ['test.integration.tests.%s' % test for test in config['tests']]
		cmd_arr = ['python2', '-m', 'unittest'] + test_list

	log.info('running: %s' % ' '.join(cmd_arr))
	p = subprocess.Popen(cmd_arr)
	p.communicate()
	return p.returncode

def edit_config_file():
	config_file_path = os.environ['TEST_CONFIG_PATH']
	config_file_path_read_only = config_file_path + '.read-only'
	with open(config_file_path_read_only, 'r') as f:
		config_yaml = yaml.safe_load(f)

	config_yaml['integration']['testNamespace'] = namespace
	if not config_yaml['integration'].get('managementServers'):
		config_yaml['integration']['managementServers'] = [default_mgmt_address]

	with open(config_file_path, 'w') as f:
		yaml.safe_dump(config_yaml, f)

def graceful_shutdown():
	log.info("Shutting down")
	if config['clear_on_failure'].lower() == "true":
		clear_environment()
	log.info("Exiting.")

def register_signals():
	signal.signal(signal.SIGTERM, graceful_shutdown)
	signal.signal(signal.SIGINT, graceful_shutdown)

def parse_args():
	parser = argparse.ArgumentParser('nvmesh-csi-tester')
	parser.add_argument('--tests', type=str, nargs='+', help='A list of test modules / cases to run in the format [test_module] or [test_module].[TestCaseClassName].[test_method_name]')
	parser.add_argument('--all', action='store_true', help='Run all available tests')
	parser.add_argument('--clean-up-before-start', action='store_true', help='If set will try to clear any resources l;eft from previous tests')
	parser.add_argument('--list', action='store_true', help='Print a list of available tests')
	parser.add_argument('--log-level', type=str, default='INFO', help='The log level that will be printed to the pod log')

	args = parser.parse_args()
	return args

def parse_env_variables(args, config):
	test_files_path = os.environ.get('TEST_FILES_PATH', '/test/integration/tests')
	config['test_files_path'] = test_files_path

	if args.list:
		return
	
	if args.all:
		config['tests'] = 'all'
	else:
		if not args.tests or len(args.tests) == 0:
			raise ValueError('No tests to run. Either --all or  --tests <test1> <test2> must be supllied')
		config['tests'] = args.tests

	return

if __name__ == "__main__":
	register_signals()
	args = parse_args()
	collect_info()
	edit_config_file()
	config = {}
	parse_env_variables(args, config)

	if args.list:
		print_available_tests(config)
		exit(0)

	log.info('Started')
	if args.clean_up_before_start:
		clear_environment()

	os.environ['TEST_STDOUT_LOG_LEVEL'] = args.log_level
	exitcode = run_test(config)

	log.info('Finished with code %s' % exitcode)
	exit(exitcode)
