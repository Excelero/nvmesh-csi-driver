#!/usr/bin/env bash

if [ -z "$num_of_volumes" ]; then
    export num_of_volumes=3
fi

test_files=(
    create_all_volume_types.sh
    create_volumes.sh
    create_fs_consumers.sh
    expand_volumes.sh
    delete_fs_consumers.sh
    delete_volumes.sh
    test_multiple_fs_consumers.sh
)

clear_environment() {
    tests/clear_environment.sh
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "Failed to clear environment"
        exit $exit_code
    fi
}

create_and_set_namespace() {
    kubectl create -f resources/nvmesh-csi-testing-namespace.json
    kubectl config set-context --current --namespace=nvmesh-csi-testing
}

run_all_tests() {
    cd tests

    for file in ${test_files[@]};
    do
        ./$file

        exit_code=$?
        if [ $exit_code -ne 0 ]; then
            echo "Test $file Failed"
            exit $exit_code
        fi
    done
}

create_and_set_namespace
clear_environment
run_all_tests

echo "All Tests Finished Successfully!"