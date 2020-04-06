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

    wait_for_object_state pod $pod_name 3 Status $status
}

wait_for_pv_status() {
    pv_name=$1
    status=$2

    wait_for_object_state pv $pv_name 5 Status $status
}

wait_for_pvc_status() {
    pvc_name=$1
    status=$2

    wait_for_object_state pvc $pvc_name 2 Status Bound
}

wait_for_pvc_to_bound() {
    wait_for_pvc_status $1 Bound
}

wait_for_object_state() {
    obj_type=$1
    obj_name=$2
    column_index=$3
    column_name=$4
    expected_value=$5

    if [ -z "$obj_name" ]; then
        echo "wait_for_object_state Error: missing $obj_type name"
        exit 3
    fi

    if [ -z "$expected_value" ]; then
        echo "wait_for_object_state Error: missing $column_name value to wait for"
        exit 3
    fi

    echo "waiting for $obj_type $obj_name to be in $column_name $expected_value..."

    current_value=$(kubectl get $obj_type | grep -e "^$obj_name\s" | awk -v col_idx=$column_index '{ print $col_idx }')
    while [ "$current_value" != "$expected_value" ];
    do
        echo "$obj_type $obj_name $column_name=$current_value - Waiting for $column_name=$expected_value.."
        sleep 1
        current_value=$(kubectl get $obj_type | grep -e "^$obj_name\s" | awk -v col_idx=$column_index '{ print $col_idx }')
    done
    echo "$obj_type $obj_name $column_name=$current_value Done."
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
        echo "Waiting for $pods pods to delete"
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

delete_all_storage_classes_except_default() {
    all_storage_classes=$(kubectl get sc --template '{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}')

    for sc in $all_storage_classes;
    do
        if [[ "$sc" != nvmesh-* ]]; then
        echo "Deleting StorageClass $sc"
            kubectl delete sc $sc
        fi
    done
}
