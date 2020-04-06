build_deployment_file() {
    DEPLOYMENT_FILE_PATH="../deployment-k8s-$k8s_version.yaml"
    RELEASE_NAME=nvmesh-csi-driver
    helm template $RELEASE_NAME ../helm/nvmesh-csi-driver --set overrideKubeVersion=$k8s_version > $DEPLOYMENT_FILE_PATH
    echo "Deployment file $DEPLOYMENT_FILE_PATH ready"
}

k8s_versions=("1.15" "1.17")

for k8s_version in ${k8s_versions[@]}
do
    build_deployment_file
done

