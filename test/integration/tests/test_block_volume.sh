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

do_io() {
    fio $VOLUME_PATH --direct=1 --rw=randrw --norandommap --randrepeat=0 --ioengine=libaio --rwmixread=100 --group_reporting --name=4ktestread --time_based --verify=0 --iodepth=1 --numjobs=1s --size=$bs --bs=$bs --runtime=$run_time --random_generator=tausworthe64
}

run_io_tests() {
    # Run
    run_time=30

    bs=4k
    do_io

    bs=8k
    do_io

    bs=128k
    do_io

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
run_io_tests
delete_pod
delete_block_volume

exit 0
