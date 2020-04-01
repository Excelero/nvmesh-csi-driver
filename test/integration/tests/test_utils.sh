#!/usr/bin/env bash

graceful_exit() {
    echo "exiting!"
    exit 0
}

trap graceful_exit SIGINT SIGTERM

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=3
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

wait_for_pod_status() {
    pod_name=$1
    status=$2

    if [ -z "$pod_name" ]; then
        echo "wait_for_pod_status error, missing pod_name as first parameter"
        exit 3
    fi

    if [ -z "$status" ]; then
        echo "wait_for_pod_status error, missing status as second parameter"
        exit 3
    fi

    echo "waiting for pod $pod_name to be in status $status..."

    pod_status=$(kubectl get pods | grep $pod_name | awk '{ print $3 }')
    while [ "$pod_status" != "$status" ];
    do
        echo "Pod $pod_name is in status $pod_status - Waiting.."
        sleep 1
        pod_status=$(kubectl get pods | grep $pod_name | awk '{ print $3 }')
    done
    echo "Pod $pod_name is in status $status"
}

wait_for_pv_status() {
    pv_name=$1
    status=$2

    if [ -z "$pod_name" ]; then
        echo "wait_for_pv_status error, missing pv_name as first parameter"
        exit 3
    fi

    if [ -z "$status" ]; then
        echo "wait_for_pv_status error, missing status as second parameter"
        exit 3
    fi

    echo "waiting for PersistentVolume $pv_name to be in status $status..."

    pv_status=$(kubectl get pv | grep $pv_name | awk '{ print $5 }')
    while [ "$pv_status" != "$status" ];
    do
        echo "PV $pv_name is in status $pv_status - Waiting.."
        sleep 1
        pv_status=$(kubectl get pv | grep $pv_name | awk '{ print $5 }')
    done
    echo "PV $pv_status is in status $status"
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

count_down() {
    i=$1
    while [[ $i -gt 0 ]]
    do
        echo $i
        let i--
        sleep 1
    done
}

delete_all_objects_of_type() {
    if [ -z $1 ]; then
        echo "No Object given"
        return
    fi

    for x in $(kubectl get $1 | awk '{ if(NR>1) print $1 }') ;
    do
        echo "deleting $x"
        kubectl delete $1 $x
    done
}

wait_with_print() {
    seconds=$1
    for i in $(seq $seconds -1 1); do
        echo "DEBUG - Waiting for another $i seconds"
        sleep 1
    done
}