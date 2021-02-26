import os

import yaml
from os import environ


class SanityTestConfig(object):
	ManagementServers = ['localhost:4000']

def parse_config(test_config):
	try:
		conf = test_config['sanity']
		SanityTestConfig.ManagementServers = conf.get('managementServers', SanityTestConfig.ManagementServers)
	except Exception as ex:
		print('Failed to parse test config. Error: %s' % ex)
		raise

def load_test_config_file():
	working_dir = os.getcwd()
	print(working_dir)
	test_config_path = environ.get('TEST_CONFIG_PATH') or '../config.yaml'
	try:
		with open(test_config_path) as fp:
			test_config = yaml.safe_load(fp)
	except Exception as ex:
		print('Failed to load test config file at %s. Error: %s' % (test_config_path, ex))
		raise

	parse_config(test_config)
