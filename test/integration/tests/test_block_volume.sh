#!/usr/bin/env bash

source ./test_utils.sh

echo "Creating a block volumes"

kubectl create -f ../resources/block_volume_consumer/block-pvc.yaml

echo "waiting for the volume to be created..."
get_volumes() {
    ready_volumes=$(kubectl get pv -o name | wc -l)
}

while [ "$ready_volumes" != "1" ];
do
    sleep 1
    get_volumes
done
echo "volume was created..."

echo "Creating a Pod to consume the Block Volume.."

kubectl create -f ../resources/block_volume_consumer/block-volume-consumer.yaml

echo "waiting for the pod to be running..."
get_running_pods() {
    ready_pods=$(kubectl get pods | grep Running | wc -l)
}

get_running_pods
while [ "$ready_pods" != "1" ];
do
    sleep 2
    get_running_pods
done
echo "The pod started successfully and is running..."

echo "Deleting the Pod"
kubectl delete pod block-volume-consumer-pod
echo "Waiting for the Pod to be removed.."

get_pods() {
    pods=$(kubectl get pods -o name | wc -l)
}

get_pods
while [ "$pods" != 0 ];
do
    sleep 2
    echo "Waiting for $pods to delete"
    get_pods
done
echo "The Pod was removed"

echo "Deleting the Block Volume"
kubectl delete pvc block-pvc
echo "Waiting for the volume to be removed.."
while [ $(kubectl get pv -o name | wc -l) != "0" ];
do
    sleep 1
done

echo "The volume was deleted"

exit 0
