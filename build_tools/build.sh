#!/usr/bin/env bash
REPO_PATH=~/nvmesh-csi-driver
servers=()
DEPLOY=false
DEPLOY_ONLY=false
DOCKER_OR_PODMAN=docker
ONLY_MANIFESTS=false
BUILD_CLUSTER_SIM=false

get_version() {
    VERSION=$(git describe | cut -f1 -d '-')
    BUILD=$(git describe | cut -f2 -d '-')
    COMMIT=$(git describe | cut -f3 -d '-')

    DRIVER_VERSION="${VERSION}-${BUILD}"
}

get_version
if [ -z "$DRIVER_VERSION" ]; then
    echo "Could not get version from git describe output: $(git describe)"
    exit 1
fi

show_help() {
    echo "Usage: ./build.sh [--servers s1 s2 s3] [--deploy] [--build-test] [--build-helm-pkg]"
    echo ""
    echo "  ./build.sh              build locally (using local docker registry)"
    echo "  --build-helm-pkg        when building locally create also helm package"
    echo "  --servers               remote servers on which to build the docker image. example: ./build.sh --servers kube-master kube-node-1 kube-node-2"
    echo "  --deploy                after build deploy using kubectl on the first server. example: ./build.sh --servers kube-master kube-node-1 kube-node-2 --deploy"
    echo "  --build-tests           build also the integration testing containers. example: ./build.sh --servers kube-master kube-node-1 kube-node-2 --deploy --build-tests"
    echo "  --build-cluster-sim     build the nvmesh-cluster-simulator locally for running sanity tests"
    echo "  --podman                use podman instead of docker for building the image"
    echo "  --only-manifests        build deployment.yaml and exit"
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
        --podman)
            DOCKER_OR_PODMAN=podman
            shift
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
        --build-helm-pkg)
            BUILD_HELM_PKG=true
            shift
        ;;
        --only-manifests)
            ONLY_MANIFESTS=true
            shift
        ;;
        --build-cluster-sim)
            BUILD_CLUSTER_SIM=true
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
    echo "Pulling latest base image"
    $DOCKER_OR_PODMAN pull registry.access.redhat.com/ubi8:latest

    echo "Building $DOCKER_OR_PODMAN image locally"
    echo "Building Version $DRIVER_VERSION commit: $COMMIT"

    cd ../
    # using the -f flag allows us to include files from a directory out of the 'context'
    # we need it because the Dockerfile is in build dir and sources are in driver dir

    $DOCKER_OR_PODMAN build -f build_tools/nvmesh-csi-driver.dockerfile . --tag excelero/nvmesh-csi-driver:$DRIVER_VERSION --build-arg VERSION=$DRIVER_VERSION --build-arg RELEASE=1

    if [ $? -ne 0 ]; then
        echo "$DOCKER_OR_PODMAN image build failed"
        exit 3
    fi
}

build_k8s_deployment_file() {
    # build Kubernetes deployment.yaml
    cd ../deploy/kubernetes/scripts
    ./build_deployment_file.sh
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "Error running build_deployment_file.sh"
        exit 2
    fi
    cd -

    return $rc
}

build_on_remote_machines() {
    sub_process_pids=()

    if [ "$BUILD_TESTS" ]; then
        BUILD_TESTS_FLAG="--build-tests"
    fi

    echo "Building on remote machines ${servers[@]}"

    for server in ${servers[@]}; do
        echo "Sending sources to remote machine ($server).."
        rsync -r --exclude ".*/" ../ $server:$REPO_PATH &> >(sed 's/^/'$server': /') &
        sub_process_pids+=($!)
    done

    # wait for all sources copy to finish
    for pid in $sub_process_pids; do
        wait $pid || failed=true
    done
    sub_process_pids=()

    if [ "$failed" = true ]; then
        echo "Failed copying sources to remote machines"
        exit 5
    fi

    for server in ${servers[@]}; do
        echo "running build.sh $BUILD_TESTS_FLAG on $server.."
        ssh $server "cd $REPO_PATH/build_tools/ ; ./build.sh $BUILD_TESTS_FLAG" &> >(sed 's/^/'$server': /') &
        sub_process_pids+=($!)
    done

    # wait build.sh to finish on all servers
    for pid in $sub_process_pids; do
        wait $pid || failed=true
    done
    sub_process_pids=()

    if [ "$failed" = true ]; then
        echo "Failed building image on remote machine"
        exit 3
    fi

    deploy
}

build_locally_nvmesh_cluster_sim() {
    cd ../test/sanity/nvmesh_cluster_simulator/mgmt-sim/
    make build
    retval=$?
    cd -
    return $retval
}

build_testsing_containers() {
    echo "Building testing containers"
    echo "running local build.sh for testing containers on remote machine ($server).."
    cd $REPO_PATH/test/integration ; ./build.sh
    cd -
}

deploy() {
    echo "Deploying YAML files.."
    kubectl delete -f ../deploy/kubernetes/deployment.yaml
    kubectl create -f ../deploy/kubernetes/deployment.yaml
}

### MAIN ###
parse_args $@

echo "Version $DRIVER_VERSION commit: $COMMIT"


if [ "$BUILD_CLUSTER_SIM" == "true" ];then
    build_locally_nvmesh_cluster_sim
    exit $?
fi

if [ "$DEPLOY_ONLY" == "true" ]; then
    if [ "$ONLY_MANIFESTS" == "true" ]; then
    echo "error in arguments: --deploy-only and --only-manifests cannot be combined"
        exit 1
    fi

    deploy
    exit 0
fi

build_k8s_deployment_file
rc=$?

if [ "$BUILD_HELM_PKG" == "true" ]; then
    echo "Building Helm Package"
    last_dir=$(pwd)
    cd ../deploy/kubernetes/helm
    helm package nvmesh-csi-driver --destination $last_dir
    cd $last_dir
fi

if [ "$ONLY_MANIFESTS" == "true" ]; then
    exit $rc
fi

if [ ${#servers[@]} -eq 0 ];then
    build_locally

    if [ "$BUILD_TESTS" ]; then
        build_testsing_containers
    fi

    if [ "$DEPLOY" == "true" ]; then
        deploy
    fi
else
    build_on_remote_machines
fi