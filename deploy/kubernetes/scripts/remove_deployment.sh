# Delete Driver
kubectl delete statefulsets nvmesh-csi-controller -n nvmesh-csi
kubectl delete daemonset nvmesh-csi-node-driver -n nvmesh-csi

# Delete Default Storage Classes
kubectl delete storageclass nvmesh-concatenated nvmesh-raid0 nvmesh-raid1 nvmesh-raid10 nvmesh-ec -n nvmesh-csi

# Delete RBAC Permission objects
kubectl delete rolebinding csi-attacher-role-cfg csi-provisioner-role-cfg csi-resizer-role-cfg -n nvmesh-csi
kubectl delete role external-attacher-cfg external-provisioner-cfg external-resizer-cfg -n nvmesh-csi
kubectl delete clusterrole external-attacher-runner external-provisioner-runner external-resizer-runner
kubectl delete clusterrolebinding csi-attacher-role csi-provisioner-role csi-resizer-role

# Delete Service and Drvier objects
kubectl delete service nvmesh-csi-controller
kubectl delete CSIDriver nvmesh-csi.excelero.com

# Delete nvmesh-csi Namespace
kubectl delete namespace nvmesh-csi