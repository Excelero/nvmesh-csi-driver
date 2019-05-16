#!/usr/bin/env bash

source ./test_utils.sh

kubectl create -f ../resources/fs_consumer/multiple-consumer-test.yaml

echo "waiting for all pods to be created..."
while [ $(kubectl get pods | grep Running | wc -l) != 2 ];
do
    sleep 1
done

echo "All pods created and running"

kubectl delete daemonset multi-consumer-test

if [ $? -ne 0 ]; then
    echo "Error deleting DaemonSet"
    exit 1
fi

echo "waiting for all pods to be deleted..."
while [ $(kubectl get pods -o name | wc -l) != 0 ];
do
    sleep 1
done

kubectl delete pvc nvmesh-vol-for-consumer-test
kubectl delete storageclass nvmesh-jbod-xfs
