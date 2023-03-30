#!/usr/bin/env bash

cd ../

export TEST_CONFIG_PATH="test/config.yaml"

print_usage() {
    echo -e "usage: $0 [test-name] [--clear-env]"

    echo -e "\n\nOptions:"
    echo -e "\t --clear-env     Clear Kubernetes and NVMesh from previous test resources - this wll delete all NVMesh volumes"
    echo -e "\t test-name       name of a specific test to run. can be module name, TesCase class, or a test function. see examples below"

    echo -e "\nExamples:"
    echo -e "\t $0 --clear-env"
    echo -e "\t $0 test.integration.tests.test_storage_class_params"
    echo -e "\t $0 test.integration.tests.test_storage_class_params.TestStorageClassParameters"
    echo -e "\t $0 test.integration.tests.test_storage_class_params.TestStorageClassParameters.test_raid0_no_params"
}

if [ $# -eq 0 ]; then
    python2 -m unittest discover test/integration 
elif [ $1 == "--help" ] || [ $1 == "-h" ]; then
    print_usage
elif [ $1 == "--clear-env" ]; then
    python2 -m unittest test.integration.tests.clear_test_environment
else
    python2 -m unittest $@
fi

exit $?