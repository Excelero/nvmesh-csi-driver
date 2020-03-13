VERSION_FILE_PATH=../../../version
VERSION=$(cat $VERSION_FILE_PATH)

if [ -z "$VERSION" ]; then
    echo "Could not find version in $VERSION_FILE_PATH"
    exit 1
fi

build_deployment_file() {
    YAML_SEPARATOR="---"
    DEPLOYMENT_FILE_PATH="../deployment$deploy_version.yaml"

    echo "Building $DEPLOYMENT_FILE_PATH"
    ORDERED_LIST_OF_YAML_FILES=(
        nvmesh-csi-namespace.yaml
        nvmesh-csi-driver.yaml
        nvmesh-configmaps.yaml
        nvmesh-credentials.yaml
        rbac-permissions.yaml
        nvmesh-storage-classes.yaml
        nvmesh-csi-deployment$deploy_version.yaml
    )

    cd ../resources

    printf "#\n# This file was generated using the 'build_deployment_file.sh' script\n#\n\n" > $DEPLOYMENT_FILE_PATH
    for filename in ${ORDERED_LIST_OF_YAML_FILES[@]}
    do
        echo "Adding $filename"
        cat $filename >> $DEPLOYMENT_FILE_PATH
        printf "\n$YAML_SEPARATOR\n" >> $DEPLOYMENT_FILE_PATH
    done

    echo "Inserting version string \"$VERSION\""

    sed -i "s/<version>/$VERSION/g" $DEPLOYMENT_FILE_PATH

    echo "Deployment file $DEPLOYMENT_FILE_PATH ready"
}


deployment_versions=("-k8s-1.15" "-k8s-1.17")

for deploy_version in ${deployment_versions[@]}
do
    build_deployment_file
done

