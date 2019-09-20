#!/usr/bin/env bash

DRIVER_VERSION=v0.0.1
REPO_PATH=~/nvmesh-csi-driver
servers=()
DEPLOY=false

show_help() {
    echo "Usage: ./build.sh [--servers s1 s2 s3] [--deploy] [--build-test]"
    echo "To build to local docker registry use: ./build.sh"
    echo "To build on remote machines using ssh use: ./build.sh --servers kube-master kube-node-1 kube-node-2"
    echo "To build and deploy on remote machines using ssh use: ./build.sh --servers kube-master kube-node-1 kube-node-2 --deploy"
    echo "To build also the integration testing containers. use: ./build.sh --servers kube-master kube-node-1 kube-node-2 --deploy --build-tests"
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
        --build-tests)
            BUILD_TESTS=true
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

    docker build -f build_tools/nvmesh-csi-driver.dockerfile . --tag excelero/nvmesh-csi-driver:$DRIVER_VERSION

    if [ $? -ne 0 ]; then
        echo "Docker image build failed"
        exit 1
    fi

    # build Kubernetes deployment.yaml
    cd deploy/kubernetes/scripts
    ./build_deployment_file.sh
}

build_on_remote_machines() {
    echo "Building on remote machines ${servers[@]}"

    for server in ${servers[@]}; do
        echo "Sending sources to remote machine ($server).."
        rsync -r ../ $server:$REPO_PATH
    done

    for server in ${servers[@]}; do
        echo "running local build.sh on remote machine ($server).."
        ssh $server "cd $REPO_PATH/build_tools/ ; ./build.sh"
    done
}

build_testsing_containers_on_remote_machines() {
    echo "Building testing containers on remote machines ${servers[@]}"

    for server in ${servers[@]}; do
        echo "running local build.sh for testing containers on remote machine ($server).."
        ssh $server "cd $REPO_PATH/test/integration ; ./build.sh"
    done
}

### MAIN ###
parse_args $@

DEPLOY_COMMAND="cd $REPO_PATH/deploy/kubernetes/scripts ; ./remove_deployment.sh ; ./deploy.sh "

if [ ${#servers[@]} -eq 0 ];then
    build_locally

    if [ "$DEPLOY" ]; then
        echo "Deploying YAML files locally.."
        eval $DEPLOY_COMMAND
    fi

else
    build_on_remote_machines

    if [ "$DEPLOY" ]; then
        echo "Deploying YAML files on ($server).."
        ssh ${servers[0]} "$DEPLOY_COMMAND"
    fi

    if [ "$BUILD_TESTS" ]; then
        build_testsing_containers_on_remote_machines
    fi
fi