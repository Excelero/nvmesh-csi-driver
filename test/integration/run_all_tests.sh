#!/usr/bin/env bash

if [ -z "$num_of_volumes" ]; then
    export num_of_volumes=3
fi

test_files=(
    create_all_volume_types.sh
    test_access_modes.sh
    create_volumes.sh
    create_fs_consumers.sh
    expand_volumes.sh
    delete_fs_consumers.sh
    delete_volumes.sh
    storage_class_params.py
    filesystem_persistency.sh
    test_block_volume.sh
    test_multiple_pods_on_same_volume.sh
    test_all_fs_types.sh
    test_migration.sh
)

clear_environment() {
    cd tests
    ./clear_environment.sh
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Failed to clear environment"
        exit $exit_code
    fi

    cd ..
}

create_and_set_namespace() {
    kubectl create namespace nvmesh-csi-testing
    kubectl config set-context --current --namespace=nvmesh-csi-testing
}

run_all_tests() {
    cd tests

    for file in ${test_files[@]};
    do
        echo "---------------------------------------- Running: $file ---------------------------------------"
        ./$file &
        child_process=$!

        wait $child_process
        exit_code=$?

        if [ $exit_code -ne 0 ]; then
            echo "-------------------------------------- Test $file Failed --------------------------------------"
            exit $exit_code
        else
            echo "------------------------------ Test $file Finished Successfully -------------------------------"
        fi

    done
}

graceful_exit() {
    echo "exiting!"
    kill -TERM "$child_process" 2>/dev/null
    clear_environment
    exit 0
}

trap graceful_exit SIGINT SIGTERM

create_and_set_namespace
clear_environment
run_all_tests

echo "All Tests Finished Successfully!"
