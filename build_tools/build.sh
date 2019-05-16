#!/usr/bin/env bash

servers=()
DEPLOY=false

show_help() {
    echo "Usage: ./build.sh [--servers s1 s2 s3] [--deploy]"
    echo "To build to local docker registry use: ./build.sh"
    echo "To build on remote machines using ssh use: ./build.sh --servers kube-master kube-node-1 kube-node-2"
    echo "To build and deploy on remote machines using ssh use: ./build.sh --servers kube-master kube-node-1 kube-node-2"
}

parse_args() {
    #temp_args=( $@ )
    while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        -s|--servers)

        shift # skip "--servers" arg

        while [[ "$1" != -* && $# -gt 0 ]]; do
            servers+=("$1")
            shift
        done

        ;;
        -d|--deploy)
            DEPLOY=true
            shift
        ;;
        -h|--help)
            show_help
            exit 0
        ;;
        *)    # unknown option
            echo "Unkown option $1"
            show_help
            exit 1
        ;;
    esac
    done
}

build_locally() {
    echo "Building Docker image locally"

    cd ../
    # using the -f flag allows us to include files from a directory out of the 'context'
    # we need it because the Dockerfile is in build dir and sources are in driver dir

    # NOTE: building while the snx VPN is running could cause network issues that will fail building the image
    docker build -f build_tools/nvmesh-csi-plugin.dockerfile . --tag excelero/nvmesh-csi-plugin:v0.0.1

    if [ $? -ne 0 ]; then
        echo "Docker image build failed"
        exit 1
    fi
}

build_on_remote_machines() {
    echo "Building on remote machines ${servers[@]}"

    for server in ${servers[@]}; do
        echo "Sending sources to remote machine ($server).."
        rsync -r ../ $server:~/nvmesh_csi_driver/
    done

    for server in ${servers[@]}; do
        echo "running local build.sh on remote machine ($server).."
        ssh $server "cd ~/nvmesh_csi_driver/build_tools/ ; ./build.sh"
    done
}

### MAIN ###
parse_args $@

if [ ${#servers[@]} -eq 0 ];then
    build_locally
else
    build_on_remote_machines

    if [ "$DEPLOY" ]; then
        echo "Deploying YAML files on ($server).."
        ssh ${servers[0]} "cd ~/nvmesh_csi_driver/deploy/kubernetes/ ; ./remove_deployment.sh ; ./deploy.sh"
    fi
fi