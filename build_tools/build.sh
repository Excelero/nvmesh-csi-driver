#!/usr/bin/env bash

DRIVER_VERSION=v0.0.2
REPO_PATH=~/nvmesh-csi-driver
servers=()
DEPLOY=false
DEPLOY_ONLY=false

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
        --deploy-only)
            DEPLOY_ONLY=true
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
        exit 3
    fi
}

build_k8s_deployment_file() {
    # build Kubernetes deployment.yaml
    cd ../deploy/kubernetes/scripts
    ./build_deployment_file.sh
    cd -
}

build_on_remote_machines() {
    if [ "$BUILD_TESTS" ]; then
        BUILD_TESTS_FLAG="--build-tests"
    fi

    echo "Building on remote machines ${servers[@]}"

    for server in ${servers[@]}; do
        echo "Sending sources to remote machine ($server).."
        rsync -r ../ $server:$REPO_PATH &> >(sed 's/^/'$server': /') &
    done

    # wait for all sources copy to finish
    for server in ${servers[@]}; do
        wait
    done

    for server in ${servers[@]}; do
        echo "running build.sh $BUILD_TESTS_FLAG on $server.."
        ssh $server "cd $REPO_PATH/build_tools/ ; ./build.sh $BUILD_TESTS_FLAG" &> >(sed 's/^/'$server': /') &
    done

    # wait build.sh to finish on all servers
    for server in ${servers[@]}; do
        wait
    done

    # deploy only on first node (kube-master) n
    if [ $DEPLOY = true ]; then
        echo "Deploying on first node"
        ssh ${servers[0]} "cd $REPO_PATH/build_tools/ ; ./build.sh --deploy-only" &> >(sed 's/^/'${servers[0]}': /')
    fi
}

build_testsing_containers() {
    echo "Building testing containers"

    for server in ${servers[@]}; do
        echo "running local build.sh for testing containers on remote machine ($server).."
        cd $REPO_PATH/test/integration ; ./build.sh
    done
}

deploy() {
    echo "Deploying YAML files.."
    cd $REPO_PATH/deploy/kubernetes/scripts

    if kubectl get namespace nvmesh-csi &>/dev/null; then
        ./remove_deployment.sh
    fi

    ./deploy.sh

    cd $REPO_PATH
}

### MAIN ###
parse_args $@

if [ $DEPLOY_ONLY = true ]; then
    deploy
    exit 0
fi

build_k8s_deployment_file

if [ ${#servers[@]} -eq 0 ];then
    build_locally

    if [ "$BUILD_TESTS" ]; then
        build_testsing_containers
    fi

    if [ $DEPLOY = true ]; then
        deploy
    fi
else
    build_on_remote_machines
fi