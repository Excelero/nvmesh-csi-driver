#!/usr/bin/env bash

source ./test_utils.sh

echo "Expanding $num_of_volumes Volumes"

for ((i=1; i<=num_of_volumes; i++))
do
   echo "Expanding Volume vol-$i"
   kubectl get pvc vol-$i -o yaml |sed -e "s/storage: 3Gi/storage: 5Gi/" | kubectl replace -f -
done

echo "waiting for all volumes to expand..."
while [ $(kubectl get pv | grep "5Gi" | wc -l) != $num_of_volumes ];
do
    sleep 1
done
echo "all volumes were created..."

echo "check file-system size in containers"

for ((i=1; i<=$num_of_volumes; i++))
do
    fs_size=""
    while [ "$fs_size" != "4.9G" ];
    do
        fs_size=$(kubectl exec -i fs-consumer-$i -- /bin/bash -c "df -Pkh /mnt/vol | tail -1 | awk '{ print \$2 }'")
        echo "fs-consumer-$i: Volume vol-$i FileSystem size is $fs_size"
        sleep 2
    done
done

exit 0