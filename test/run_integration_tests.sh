#!/usr/bin/env bash

show_help() {
    echo "Usage: ./run_integration_tests.sh --master kube-master.excelero.com"
}

parse_args() {
    while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        -m|--master)
        server="$2"
        shift # past argument
        shift # past value
        ;;
        -h|--help)
            show_help
            exit 0
        ;;
        *)    # unknown option
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
rsync -r integration/ $server:~/k8s_csi_integration/

echo "Running test on remote machine ($server)"
ssh $server "cd ~/k8s_csi_integration ; ./run_all_tests.sh"
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "Finished Running Tests on remote machine ($server)"
else
    echo "Integration Tests Failed"
    exit $exit_code
fi
