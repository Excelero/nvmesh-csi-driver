#!/usr/bin/env bash

read -r -d '' create_volume_template << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: vol-{index}
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 3Gi
  storageClassName: nvmesh-raid1
EOM

for i in {1..30} ; do
    echo "Creating Volume vol-$i"
    echo "$create_volume_template" | sed -e "s/{index}/$i/" | kubectl create -f -
done

echo "waiting for all volumes to be created..."
while [ $(kubectl get pv -o name | wc -l) != 30 ];
do
    sleep 1
done
echo "all volumes were created..."

for i in {1..30} ; do
    echo "Deleting pvc vol-$i"
    kubectl delete pvc vol-$i
done

echo "waiting for all volumes to be deleted..."
while [ $(kubectl get pv -o name | wc -l) != "0" ];
do
    sleep 1
done
echo "all volumes were deleted..."

exit 0
