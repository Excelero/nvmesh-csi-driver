#!/usr/bin/env bash

clear_old_deployment() {
    kubectl delete service nvmesh-csi-controller
    kubectl delete serviceaccount csi-attacher
    kubectl delete serviceaccount csi-provisioner
    kubectl delete serviceaccount nvmesh-csi
    kubectl delete statefulsets nvmesh-csi-controller

    #kubectl delete pods,services,serviceaccounts,statefulsets -l app=nvmesh-csi
}

build() {
    ./docker_build.sh
}

deploy() {
    kubectl create -f ../deploy/kubernetes/csi-nvmesh-deployment.yaml
}

show_logs() {
    # wait for pod to start
    sleep 0.5

    kubectl logs nvmesh-csi-controller-0 -c nvmesh-csi-plugin --follow
}


### MAIN ###
############
cd ../
clear_old_deployment
build
deploy
show_logs
