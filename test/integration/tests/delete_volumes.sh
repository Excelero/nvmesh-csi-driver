#!/usr/bin/env bash

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=30
fi

for ((i=1; i<=num_of_volumes; i++))
do
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
