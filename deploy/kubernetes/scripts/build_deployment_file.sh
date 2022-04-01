build_deployment_file() {
    DEPLOYMENT_FILE_PATH="../deployment.yaml"
    RELEASE_NAME=nvmesh-csi-driver
    helm template $RELEASE_NAME ../helm/nvmesh-csi-driver --namespace nvmesh-csi --set overrideKubeVersion=$k8s_version > $DEPLOYMENT_FILE_PATH
    echo "Deployment file $DEPLOYMENT_FILE_PATH ready"
}

check_herm_exists() {
    if ! which helm; then
        echo "Cannot compile yaml deployment files - failed to find helm"
        exit 1
    fi
}

check_herm_exists
build_deployment_file

./post_process_deployment.py

