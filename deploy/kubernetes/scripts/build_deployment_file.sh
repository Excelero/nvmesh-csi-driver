
RELEASE_NAME=nvmesh-csi-driver
VALUES_PATH="../helm/nvmesh-csi-driver/values.yaml"
VALUES_DEV_PATH="../helm/nvmesh-csi-driver/values-dev.yaml"

build_deployment_file() {
    DEPLOYMENT_FILE_PATH="../deployment.yaml"
    helm template $RELEASE_NAME ../helm/nvmesh-csi-driver --namespace nvmesh-csi --set overrideKubeVersion=$k8s_version > $DEPLOYMENT_FILE_PATH
    echo "Deployment file $DEPLOYMENT_FILE_PATH ready"
}

build_dev_deployment_file() {
    DEPLOYMENT_FILE_PATH="../deployment_dev.yaml"

    if [ ! -f $VALUES_DEV_PATH ]; then
        cp $VALUES_PATH $VALUES_DEV_PATH

        sed -i '1 i\# DEV OVERRIDES\nappVersion: v1.3.0-dev\nk8sVersion: "1.25"\n\n' $VALUES_DEV_PATH
        echo "Generated new $VALUES_DEV_PATH file"
    fi

    helm template $RELEASE_NAME ../helm/nvmesh-csi-driver -f ../helm/nvmesh-csi-driver/values-dev.yaml --namespace nvmesh-csi --set overrideKubeVersion=$k8s_version > $DEPLOYMENT_FILE_PATH
    echo "Dev Deployment file $DEPLOYMENT_FILE_PATH ready"
}

check_helm_exists() {
    if ! which helm; then
        echo "Cannot compile yaml deployment files - failed to find helm"
        exit 1
    fi
}

check_helm_exists
build_deployment_file
build_dev_deployment_file
./post_process_deployment.py

