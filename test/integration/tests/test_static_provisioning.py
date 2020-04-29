#!/usr/bin/env python2

import unittest

from NVMeshSDK.Consts import RAIDLevels
from NVMeshSDK.Entities.Volume import Volume
from utils import TestUtils, KubeUtils, NVMeshUtils, core_api

logger = TestUtils.get_logger()

GiB = 1024*1024*1024
class TestStaticProvisioning(unittest.TestCase):
	def test_static_provisioning(self):
		# Create NVMesh Volume
		nvmesh_volume_name = "vol-static-prov"
		volume = Volume(name=nvmesh_volume_name,
						RAIDLevel=RAIDLevels.STRIPED_AND_MIRRORED_RAID_10,
						VPG='DEFAULT_RAID_10_VPG',
						capacity=5*GiB,
						description="Volume for CSI Driver Static Provisioning"
						)
		err, out = NVMeshUtils.getVolumeAPI().save([volume])
		self.assertIsNone(err, 'Error Creating NVMesh Volume. %s' % err)
		create_res = out[0]
		self.assertTrue(create_res['success'], 'Error Creating NVMesh Volume. %s' % create_res['error'])

		self.addCleanup(lambda: NVMeshUtils.getVolumeAPI().delete([volume]))

		# Create PV
		pv_name = 'pv-name-in-k8s'
		accessModes = ['ReadWriteOnce']
		volume_size = '5Gi'
		sc_name = 'nvmesh-raid10'
		pv = {
			'apiVersion': 'v1',
			'kind': 'PersistentVolume',
			'metadata': {
				'name': pv_name
			},
			'spec': {
				'accessModes': accessModes,
				'persistentVolumeReclaimPolicy': 'Retain',
				'capacity': {
					'storage': volume_size
				},
				'volumeMode': 'Block',
				'storageClassName': sc_name,
				'csi': {
					'driver': 'nvmesh-csi.excelero.com',
					'volumeHandle': nvmesh_volume_name
				}
			}
		}

		core_api.create_persistent_volume(pv)

		self.addCleanup(lambda: core_api.delete_persistent_volume(pv_name))

		pv_list = core_api.list_persistent_volume(field_selector='metadata.name={}'.format(pv_name))
		self.assertIsNotNone(pv_list)
		self.assertTrue(len(pv_list.items))
		self.assertEqual(pv_list.items[0].metadata.name, pv_name)

		# Create PVC
		pvc_name = 'pvc-static-prov'
		KubeUtils.create_pvc_and_wait_to_bound(self,
											   pvc_name,
											   sc_name,
											   access_modes=accessModes,
											   storage=volume_size,
											   volumeMode='Block')

		self.addCleanup(lambda: KubeUtils.delete_pvc(pvc_name))

		# Create Consumer pod
		pod_name = 'pod-static-prov'
		cmd = 'echo hello ; while true ; do wait 1; done'
		pod = KubeUtils.get_shell_pod_template(pod_name, pvc_name, cmd, volume_mode_block=True)
		KubeUtils.create_pod(pod)

		def cleanup_pod():
			KubeUtils.delete_pod(pod_name)
			KubeUtils.wait_for_pod_to_delete(pod_name)

		self.addCleanup(cleanup_pod)

		KubeUtils.wait_for_pod_to_be_running(pod_name)



if __name__ == '__main__':
	TestUtils.run_unittest()
