#!/usr/bin/env bash

show_logs() {
    # wait for pod to start
    sleep 1

    kubectl logs nvmesh-csi-controller-0 -c nvmesh-csi-plugin --follow
}


### MAIN ###
############

./clear_old_deployment.sh

cd ../build_tools
./docker_build.sh

cd ../deploy/kubernetes/
./deploy.sh

