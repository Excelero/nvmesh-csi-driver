#!/usr/bin/env bash

source ./test_utils.sh

create_block_volume() {
    echo "Creating a block volumes"

    kubectl create -f ../resources/block_volume_consumer/block-pvc.yaml
    wait_for_volumes 1
}

create_pod() {
    echo "Creating a Pod to consume the Block Volume.."

    kubectl create -f ../resources/block_volume_consumer/block-volume-consumer.yaml

    wait_for_pods 1
}

delete_pod() {
    echo "Deleting the Pod"
    kubectl delete pod block-volume-consumer-pod
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
create_pod
delete_pod
delete_block_volume

exit 0
