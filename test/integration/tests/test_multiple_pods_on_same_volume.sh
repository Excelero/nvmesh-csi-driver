#!/usr/bin/env bash

source ./test_utils.sh


create_block_volume() {
    echo "Creating a block volume"

    kubectl create -f ../resources/block_volume_consumer/block-pvc.yaml
    wait_for_volumes 1
}

create_replica_set() {
    echo "Creating a ReplicaSet to consume the Block Volume using multiple Pods.."

    kubectl create -f ../resources/block_volume_consumer/multiple-block-consumers.yaml

    wait_for_pods 3
}

delete_replica_set() {
    echo "Deleting the ReplicaSet"
    kubectl delete replicaset block-multi-consumer-rs
    wait_for_pods_to_be_removed
}

delete_block_volume() {
    echo "Deleting the Block Volume"
    kubectl delete pvc block-pvc
    echo "Waiting for the volume to be removed.."
    while [ $(kubectl get pv -o name | wc -l) != "0" ];
    do
        sleep 1
    done

    echo "The volume was deleted"
}

create_block_volume
create_replica_set
delete_replica_set
delete_block_volume

exit 0