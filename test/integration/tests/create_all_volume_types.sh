#!/usr/bin/env bash

source ./test_utils.sh

RAID_TYPES=(concatenated raid0 raid1 raid10 ec)
read -r -d '' create_volume_template << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nvmesh-{raid_type}
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - ReadWriteMany
  resources:
    requests:
      storage: 3Gi
  storageClassName: nvmesh-{raid_type}
EOM

for raid_type in ${RAID_TYPES[@]} ; do
    echo "Creating Volume of type $raid_type"
    echo "$create_volume_template" | sed -e "s/{raid_type}/$raid_type/" | kubectl create -f -
done

echo "waiting for all volumes to be created..."
while [ $(kubectl get pv -o name | wc -l) != "${#RAID_TYPES[@]}" ];
do
    sleep 1
done

for raid_type in ${RAID_TYPES[@]} ; do
    echo "Deleting pvc nvmesh-$raid_type"
    kubectl delete pvc nvmesh-$raid_type
done

echo "waiting for all volumes to be deleted..."
volumes_left=$(kubectl get pv -o name | wc -l)
while [ "$volumes_left" != "0" ];
do
    echo "$volumes_left Volumes still not deleted.."
    sleep 1
    volumes_left=$(kubectl get pv -o name | wc -l)
done

exit 0
