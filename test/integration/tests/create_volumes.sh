#!/usr/bin/env bash

source ./test_utils.sh

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

echo "Creating $num_of_volumes Volumes"

for ((i=1; i<=num_of_volumes; i++))
do
   echo "Creating Volume vol-$i"
   echo "$create_volume_template" | sed -e "s/{index}/$i/" | kubectl create -f -
done

echo "waiting for all volumes to be created..."

wait_for_volumes "$num_of_volumes"

echo "all volumes were created..."


exit 0
