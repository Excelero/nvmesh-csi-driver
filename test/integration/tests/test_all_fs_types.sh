#!/usr/bin/env bash

source ./test_utils.sh

echo "Creating FileSystem Consumers"

echo "Creating Volumes and Pods for all File Systems"

kubectl create -f ../resources/fs_consumer/test_fs_consumers.yaml

wait_for_volumes 3
wait_for_pods 3


kubectl delete pod fs-ext4-consumer fs-ext3-consumer fs-xfs-consumer
kubectl delete pvc nvmesh-ext3 nvmesh-ext4 nvmesh-xfs
kubectl delete storageclass nvmesh-ext3 nvmesh-ext4 nvmesh-xfs

wait_for_pods_to_be_removed
wait_for_volumes 0




