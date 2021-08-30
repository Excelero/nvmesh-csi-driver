import json
import logging
import os
import select
import sys
import time
from signal import SIGTERM

import requests
import subprocess
from threading import Thread

from requests import ConnectionError


class NVMeshCluster(object):
	def __init__(self, name, http_port=4000, ws_port=4001, clients=None, options=None, log_level=logging.DEBUG):
		self.name = name
		self.http_port = http_port
		self.ws_port = ws_port
		self.clients = clients
		self.options = options
		self.thread = None
		self.logger = self.get_logger(log_level)
		self.should_continue = True
		self.sub_process = None

	def get_logger(self, log_level):
		logger = logging.getLogger('Cluster {}'.format(self.name))
		handler = logging.StreamHandler()
		formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
		handler.setFormatter(formatter)
		logger.addHandler(handler)
		logger.setLevel(log_level)
		return logger

	def run_cmd_in_sub_process(self, command_string):
		self.logger.debug('running cmd: %s' % command_string)
		process = subprocess.Popen(command_string, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
		return process

	def stream_output(self, p):
		def stream_logs(pipe, logger):
			for line in iter(pipe.readline, b''):
				logger.info(line)

		t = Thread(name='{}_stream_logs'.format(self.name), target=stream_logs, args=(p.stdout, self.logger))
		t.start()
		return t

	def start(self):
		self.logger.info('Starting NVMeshCluster {} on http_port: {} ws_port: {}'.format(self.name, self.http_port, self.ws_port))
		cmd = 'docker run --rm --net host --name {name} mgmt-simulator-for-csi:dev app.js --http-port {http_port} --ws-port {ws_port}'.format(
			name=self.name, http_port=self.http_port, ws_port=self.ws_port)

		if self.clients:
			cmd += ' --clients {}'.format(' '.join(self.clients))

		if self.options:
			cmd += ' --options \'{}\''.format(json.dumps(self.options))

		def run():
			self.sub_process = self.run_cmd_in_sub_process(cmd)
			stream_thread = self.stream_output(self.sub_process)

			while self.should_continue:
				stream_thread.join(1)

			self.logger.debug('Cluster ended with exit code: {}'.format(self.sub_process.returncode))
			self.logger.info('Cluster stopped')

		self.thread = Thread(target=run)
		self.thread.start()

	def wait_until_is_alive(self):
		self.logger.info('Waiting for cluster to be alive')
		while True:
			try:
				if self.is_alive():
					break
			except ConnectionError as ex:
				pass
		self.logger.info('Cluster is alive')

	def is_alive(self):
		mgmt_server = self.get_mgmt_server_string()
		url = 'https://{}/isAlive'.format(mgmt_server)
		res = requests.get(url, verify=False)
		return res.status_code == 200

	def stop(self):
		self.should_continue = False
		cmd = 'docker stop -t {timeout} {container}'.format(container=self.name, timeout=2)
		ret = subprocess.call(cmd, shell=True)
		self.logger.debug('docker stop returned {}'.format(ret))
		try:
			self.logger.debug('sending SIGTERM to process %d' % self.sub_process.pid)
			os.kill(int(self.sub_process.pid), SIGTERM)
		except:
			pass

		while self.thread.isAlive():
			self.logger.debug('waiting for streaming thread to finish..')
			self.thread.join(1)

	def get_mgmt_server_string(self):
		return 'localhost:{}'.format(self.http_port)

def create_clusters(num_of_clusters, num_of_client_per_cluster, name_prefix='nvmesh'):
	print('Creating {} NVMesh Clusters with {} clients each'.format(num_of_clusters, num_of_client_per_cluster))

	clusters = []
	http_port = 4000
	for i in range(1, num_of_clusters + 1):
		http_port += 10
		ws_port = http_port + 1

		cluster_name = '%s%d' % (name_prefix, i)
		clients = []
		for j in range(1, num_of_client_per_cluster + 1):
			clients.append('%s_%d-n%d' % (name_prefix, i, j))

		cluster = NVMeshCluster(cluster_name, http_port=http_port, ws_port=ws_port, clients=clients)
		clusters.append(cluster)


	return clusters

def get_config_topology_from_cluster_list(clusters):
	topology = {
		"zones": {
		}
	}
	for cluster in clusters:
		topology['zones'][cluster.name] = {
			"management": {
				"servers": cluster.get_mgmt_server_string(),
				"ws_port": cluster.ws_port
			}
		}
	return topology


def example_1_create_2_clusters():
	# Usage Example - start two clusters
	cluster1 = NVMeshCluster('nvmesh1', clients=['scale-1.excelero.com', 'scale-2.excelero.com'])
	cluster2 = NVMeshCluster('nvmesh2', http_port=5000, ws_port=5001, clients=['scale-3.excelero.com', 'scale-4.excelero.com'])

	cluster1.start()
	cluster2.start()

	cluster1.wait_until_is_alive()
	cluster2.wait_until_is_alive()

	# let them run for a few seconds to see streaming logs..
	time.sleep(5)

	cluster1.stop()
	cluster2.stop()

def example_2_create_multiple_clusters():
	clusters = create_clusters(num_of_clusters=5, num_of_client_per_cluster=3)
	for cluster in clusters:
		cluster.start()

	for cluster in clusters:
		cluster.wait_until_is_alive()

	for i in range(10):
		print('waiting.. %d' % i)
		time.sleep(1)

	for cluster in clusters:
		cluster.stop()


if __name__ == '__main__':
	# example_1_create_2_clusters()

	example_2_create_multiple_clusters()
