build_deployment_file() {
    DEPLOYMENT_FILE_PATH="../deployment.yaml"
    RELEASE_NAME=nvmesh-csi-driver
    helm template $RELEASE_NAME ../helm/nvmesh-csi-driver --set overrideKubeVersion=$k8s_version > $DEPLOYMENT_FILE_PATH
    echo "Deployment file $DEPLOYMENT_FILE_PATH ready"
}

build_deployment_file

./post_process_deployment.py

