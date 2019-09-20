
kubectl delete service nvmesh-csi-controller -n nvmesh-csi
kubectl delete statefulsets nvmesh-csi-controller -n nvmesh-csi
kubectl delete daemonset nvmesh-csi-node-driver -n nvmesh-csi
kubectl delete storageclass nvmesh-concatenated nvmesh-raid0 nvmesh-raid1 nvmesh-raid10 nvmesh-ec -n nvmesh-csi
kubectl delete service nvmesh-csi-controller
kubectl delete CSIDriver nvmesh-csi.excelero.com
kubectl delete namespace nvmesh-csi