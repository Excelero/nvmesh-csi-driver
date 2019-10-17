#!/usr/bin/env bash

graceful_exit() {
    echo "exiting!"
    exit 0
}

trap graceful_exit SIGINT SIGTERM

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=30
fi

get_running_pods() {
    running_pods_count=$(kubectl get pods | grep Running | wc -l)
}

wait_for_pods() {
    num_of_pods="$1"
    echo "waiting for $num_of_pods pods to be running..."

    get_running_pods
    while [ "$running_pods_count" != "$num_of_pods" ];
    do
        sleep 1
        get_running_pods
    done
    echo "$num_of_pods pods have started successfully and are running..."
}

get_volumes_count() {
    volumes_count=$(kubectl get pv -o name | wc -l)
}

wait_for_volumes() {
    num_of_volumes="$1"

    echo "waiting for volume count to reach $num_of_volumes"
    get_volumes_count

    while [ "$volumes_count" != "$num_of_volumes" ];
    do
        echo "Volume Count $volumes_count"
        sleep 1
        get_volumes_count
    done
    echo "reached $num_of_volumes volumes"
}


wait_for_pods_to_be_removed() {
    echo "Waiting for all Pods to be removed.."

    get_pods() {
        pods=$(kubectl get pods -o name | wc -l)
    }

    get_pods
    while [ "$pods" != 0 ];
    do
        sleep 1
        echo "Waiting for $pods to delete"
        get_pods
    done
    echo "all Pods removed"
}