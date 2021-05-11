import json
import logging

import config
from topology_fetcher import TopologyFetcher, Topology
import config_map_api


TOPOLOGY_CONFIG_MAP_NAME = 'nvmesh-csi-topology'

logger = logging.getLogger('topology-service')
logger.setLevel(logging.DEBUG)

class TopologyService(object):
    '''
    TopologyService is responsible for monitoring the ManagementServers on each zone and updating the csi-topology ConfigMap
    Each of the nodes CSI Node Drivers will find out it's zone from the ConfigMap
    '''
    def __init__(self):
        config_map_api.init()

        self.topology = Topology()
        self.load_zones_configuration()
        self.load_topology_from_config_map()
        self.topology.on_change_listeners.append(self.save_topology)
        self.fetcher = TopologyFetcher(self.topology)

    def run(self):
        self.fetcher.fetch_and_listen_for_changes_on_all_zones()


    def stop(self):
        self.fetcher.stop()

    #Loads the user configured zones and their management servers
    def load_zones_configuration(self):
        topology = config.Config.TOPOLOGY
        if not topology:
            return
        for zone_id, zone_config in topology.get('zones').items():
            self.topology.add_zone_config(zone_id, zone_config)

    #Loads the topology from the config map
    def load_topology_from_config_map(self):
        logger.info('Loading topology from ConfigMap')

        try:
            config_map = config_map_api.load(TOPOLOGY_CONFIG_MAP_NAME)
        except config_map_api.ConfigMapNotFound as ex:
            config_map = config_map_api.create(TOPOLOGY_CONFIG_MAP_NAME, {'zones': "{}"})

        data = config_map.data
        zones = json.loads(data.get('zones'))
        for zone_id, zone in zones.items():
            if zone in self.topology.zones.keys():
                self.topology.add_nodes_for_zone(zone_id, zone.get('nodes'))
            else:
                logger.warning('Zone {} from {} ConfigMap was not found in the topology configuration, this zone was probably removed or renamed'.format(zone_id, TOPOLOGY_CONFIG_MAP_NAME))

        logger.debug('Finished loading topology from ConfigMap')

    def save_topology(self):
        zones = self.topology.get_serializable_topology()

        config_map_data = {
            'zones': json.dumps(zones, indent=2, sort_keys=True)
        }

        try:
            config_map = config_map_api.update(TOPOLOGY_CONFIG_MAP_NAME, config_map_data)
        except config_map_api.ConfigMapNotFound as ex:
            config_map = config_map_api.create(TOPOLOGY_CONFIG_MAP_NAME, config_map_data)
        return config_map


if __name__ == "__main__":
    topology_sever = TopologyService()

