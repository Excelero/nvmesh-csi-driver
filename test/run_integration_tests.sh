#!/usr/bin/env bash

show_help() {
    echo "Usage: ./run_integration_tests.sh --master kube-master.excelero.com [--num-of-volumes <n>] [--no-ec-volumes]"
    echo ""
    echo -e "\t --master \t\t required | the master node hostname or IP address (where kubectl is available)"
    echo -e "\t --num-of-volumes \t optional | the number of volumes and pods to test create, attach, expand, detach and delete"
    echo -e "\t --no-ec-volumes \t optional | skip testing of EC volumes type. Can be useful if the NVMesh testing environment doesn't have enough resources for EC volumes"
    echo -e "\t --skip-clear-env \t optional | skip clearing the test environment of old objects - this could make the tests fail"

}

no_ec_volumes=false

parse_args() {
    while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        -m|--master)
            server="$2"
            shift
            shift
        ;;
        --no-ec-volumes)
            no_ec_volumes=true
            shift
        ;;
        --num-of-volumes)
            num_of_volumes="$2"
            shift
            shift
        ;;
        --skip-clear-env)
            skip_clear_env=true
            shift
        ;;
        -h|--help)
            show_help
            exit 0
        ;;
        *)  # unknown option
            show_help
            exit 1
        ;;
    esac
    done

}

parse_args $@

if [ -z "$server" ];then
    echo "missing --master argument"
    show_help
    exit 1
fi

echo "Running test on server $server"
echo "Copying sources to $server.."
rsync -r ../test $server:~/k8s_csi_integration/

if [ -z "$skip_clear_env" ]; then
    echo "Clearing Test Environment"
    ssh $server "cd ~/k8s_csi_integration ; python -m test.integration.tests.clear_test_environment"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to clear environment.\nTo start the tests anyway run again with the flag --skip-clear-env"
        exit 1
    fi
else
    echo "Skipping Clearing of Test Environment"
fi

echo "Running test on remote machine ($server)"
time ssh $server "export num_of_volumes=$num_of_volumes ; export no_ec_volumes=$no_ec_volumes ; cd ~/k8s_csi_integration  ; python -m unittest discover test/integration/tests"
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "Finished Running Tests on remote machine ($server)"
else
    echo "Integration Tests Failed"
    exit $exit_code
fi
