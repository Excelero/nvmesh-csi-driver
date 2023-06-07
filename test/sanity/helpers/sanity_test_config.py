import os

import yaml
from os import environ


class SanityTestConfig(object):
	LogLevel = 1

def parse_config(test_config):
	try:
		conf = test_config['sanity']
		SanityTestConfig.LogLevel = conf.get('logLevel', 1)
	except Exception as ex:
		print('Failed to parse test config. Error: %s' % ex)
		raise

def load_test_config_file():
	working_dir = os.getcwd()
	print(working_dir)
	test_config_path = environ.get('TEST_CONFIG_PATH') or '../config.yaml'
	try:
		print('Loading config from %s' % test_config_path)
		import subprocess
		print(subprocess.check_output(['ls','-lsa','/config']))
		with open(test_config_path) as fp:
			test_config = yaml.safe_load(fp)
	except Exception as ex:
		print('Failed to load test config file at %s. CWD: %s Error: %s' % (test_config_path, os.getcwd(), ex))
		raise

	parse_config(test_config)