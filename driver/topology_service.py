import json
import logging
import os
import threading
from threading import Thread

import config
from common import BackoffDelay, BackoffDelayWithStopEvent
from zone_topology_fetcher import ZoneTopologyFetcherThread
from topology import Topology

import config_map_api

logger = logging.getLogger('topology-service')
logger.setLevel(logging.DEBUG)

class TopologyService(object):
    '''
    TopologyService is responsible for monitoring the ManagementServers on each zone and updating the csi-topology ConfigMap
    Each of the nodes CSI Node Drivers will find out it's zone from the ConfigMap
    '''
    def __init__(self):
        config_map_api.init()
        self.ws_threads = {}
        self.topology = Topology()
        self.topology.on_change_listeners.append(self.save_topology_to_config_map)
        self.config_map_event_stream = None
        self.config_map_event_watcher = None
        self.config_map_watcher_thread = Thread(name='config-map-watcher', target=self.watch_topology_config_map)
        self.stop_event = threading.Event()

    def run(self):
        self.load_zones_configuration()
        self.load_topology_from_config_map()
        self.config_map_watcher_thread.start()

    def start_listening_thread_for_zone(self, zone_id, zone_config, topology):
        t = ZoneTopologyFetcherThread(zone_id, zone_config, topology, self.stop_event)
        self.ws_threads[zone_id] = t
        t.start()

    def stop_listening_thread_for_zone(self, zone_id):
        thread = self.ws_threads[zone_id]
        thread.stop()
        return thread

    def stop(self):
        self.stop_event.set()
        try:
            logger.debug('stop(): Stop watching ConfigMap changes')
            if self.config_map_event_watcher:
                self.config_map_event_watcher.stop()
        except Exception as ex:
            logger.exception(ex)

        logger.debug('stop(): Waiting for {} zone threads to finish'.format(len(self.ws_threads.keys())))
        for t in self.ws_threads.values():
            t.stop()

        for zone_id, t in self.ws_threads.items():
            logger.debug('stop(): Waiting for zone {} thread to finish'.format(zone_id))
            t.join()

        self.config_map_watcher_thread.join()
        logger.debug('stop(): All threads in topology service finished')

    def on_config_map_update_event(self, event):
        event_type = event['type']
        if event_type in ['ADDED', 'MODIFIED']:
            updated_config_map = event['raw_object']
            updated_topology_config = updated_config_map['data'].get('topology')

            if event_type != 'ADDED':
                logger.info('ConfigMap %s was %s' % (config.Config.CSI_CONFIG_MAP_NAME, event_type.lower()))
                logger.debug('updated_topology_config = \n%s' % updated_topology_config)

            if not updated_topology_config:
                config.Config.TOPOLOGY = None
                config.ConfigValidator.validate_and_set_topology()
                return

            try:
                topology_conf = json.loads(updated_topology_config)
            except Exception as ex:
                logger.error('Failed to load JSON topology configuration. Error: %s' % ex)
                return

            try:
                config.ConfigValidator.validate_topology_config(topology_conf)
                config.Config.TOPOLOGY = topology_conf
                self.load_zones_configuration()
            except Exception as ex:
                logger.error('Failed to load updated topology configuration. Error: %s' % ex)
        else:
            logger.debug('ConfigMap %s event %s: %s' % (config.Config.CSI_CONFIG_MAP_NAME, event_type.lower(), event))

    def watch_topology_config_map(self):
        if os.environ.get('DEVELOPMENT'):
            return
        logger.info('Listening for changes on ConfigMap %s' % config.Config.CSI_CONFIG_MAP_NAME)
        backoff = BackoffDelayWithStopEvent(event=self.stop_event, initial_delay=5, factor=2, max_delay=60)
        while not self.stop_event.is_set():
            try:
                stream, self.config_map_event_watcher = config_map_api.watch(config.Config.CSI_CONFIG_MAP_NAME, timeout_seconds=10)
                for raw_event in stream:
                    backoff.reset()
                    self.on_config_map_update_event(raw_event)
            except Exception as ex:
                logger.error('{} ConfigMap watcher encountered an error, will retry in {} seconds. Error: {}'.format(
                    config.Config.CSI_CONFIG_MAP_NAME, backoff.current_delay, ex))
                backoff.wait()

    # Loads the user configured zones and their management servers
    def load_zones_configuration(self):
        new_topology = config.Config.TOPOLOGY
        if not new_topology:
            return

        with self.topology.lock:
            existing_zones = set(self.topology.zones.keys())
            for zone_id, zone_config in new_topology.get('zones').items():
                if zone_id not in existing_zones:
                    self.add_new_zone(zone_id, zone_config)
                else:
                    # Zone exists - check if changed
                    old_zone_config_str = json.dumps(self.topology.zones[zone_id].get('management'), sort_keys=True)
                    new_zone_config_str = json.dumps(zone_config.get('management'), sort_keys=True)
                    # logger.debug('Comparing zone %s config: new=%s old=%s' % (zone_id, new_zone_config_str, old_zone_config_str))
                    if new_zone_config_str != old_zone_config_str:
                        self.update_existing_zone(zone_id, zone_config)

                existing_zones.discard(zone_id)

            # any existing zones that were not found in the new topology are to be removed
            for zone_to_remove in existing_zones:
                self.remove_zone(zone_to_remove)

    def add_new_zone(self, zone_id, zone_config):
        logger.info('Adding new zone %s' % zone_id)
        zone_config['nodes'] = set()
        self.topology.zones[zone_id] = zone_config
        self.start_listening_thread_for_zone(zone_id, zone_config, self.topology)

    def update_existing_zone(self, zone_id, zone_config):
        logger.info('Updating existing zone %s' % zone_id)
        zone_config['nodes'] = set()
        self.topology.zones[zone_id] = zone_config

        def stop_current_thread_and_start_new_one():
            current_thread = self.stop_listening_thread_for_zone(zone_id)
            logger.debug('waiting for zone %s thread to join' % zone_id)
            current_thread.join()
            logger.debug('zone %s thread finished - starting new thread' % zone_id)
            self.start_listening_thread_for_zone(zone_id, zone_config, self.topology)

        Thread(name='zone-replace-thread', target=stop_current_thread_and_start_new_one).start()

    def remove_zone(self, zone_id):
        logger.info('Removing zone %s' % zone_id)
        # This method does not waits for the thread to join
        self.stop_listening_thread_for_zone(zone_id)
        self.topology.remove_zone(zone_id)

    # Loads the topology from the config map
    def load_topology_from_config_map(self):
        logger.info('Loading topology from ConfigMap')

        try:
            config_map = config_map_api.load(config.Config.TOPOLOGY_CONFIG_MAP_NAME)
        except config_map_api.ConfigMapNotFound:
            try:
                config_map = config_map_api.create(config.Config.TOPOLOGY_CONFIG_MAP_NAME, {'zones': "{}"})
            except config_map_api.ConfigMapAlreadyExists:
                config_map = config_map_api.load(config.Config.TOPOLOGY_CONFIG_MAP_NAME)

        data = config_map.data
        zones = json.loads(data.get('zones'))
        for zone_id, zone in zones.items():
            if zone in self.topology.zones.keys():
                self.topology.add_nodes_for_zone(zone_id, zone.get('nodes'))
            else:
                logger.warning('Zone {} from {} ConfigMap was not found in the topology configuration, this zone was probably removed or renamed'.format(zone_id, config.Config.TOPOLOGY_CONFIG_MAP_NAME))

        logger.debug('Finished loading topology from ConfigMap')

    def save_topology_to_config_map(self):
        zones = self.topology.get_serializable_topology()

        config_map_data = {
            'zones': json.dumps(zones, indent=2, sort_keys=True)
        }

        try:
            config_map = config_map_api.update(config.Config.TOPOLOGY_CONFIG_MAP_NAME, config_map_data)
        except config_map_api.ConfigMapNotFound as ex:
            config_map = config_map_api.create(config.Config.TOPOLOGY_CONFIG_MAP_NAME, config_map_data)
        return config_map


if __name__ == "__main__":
    topology_sever = TopologyService()

