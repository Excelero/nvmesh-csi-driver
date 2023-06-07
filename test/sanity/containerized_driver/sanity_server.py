# This is intended to wrap the init file of the CSI Driver while preparing and mocking some of the services such as kubenretes API

# prepare imports 
from test.sanity.helpers import config_map_api_mock

from driver.server import get_driver_type, NVMeshCSIDriverServer

if __name__ == '__main__':
	print("Starting Sanity CSI Driver")
	driver_type = get_driver_type()
	driver = NVMeshCSIDriverServer(driver_type)
	driver.serve()
	driver.logger.info("Server Process Finished")
