YAML_SEPARATOR="---"
DEPLOYMENT_FILE_PATH="../deployment.yaml"
ORDERED_LIST_OF_YAML_FILES=(
    nvmesh-csi-namespace.yaml
    nvmesh-csi-driver.yaml
    nvmesh-configmaps.yaml
    nvmesh-credentials.yaml
    rbac-permissions.yaml
    nvmesh-csi-deployment.yaml
    nvmesh-storage-classes.yaml
)
cd ../resources

printf "#\n# This file was generated using the 'build_deployment_file.sh' script'\n#\n\n" > $DEPLOYMENT_FILE_PATH
for filename in ${ORDERED_LIST_OF_YAML_FILES[@]}
do
    echo "Adding $filename"
    cat $filename >> $DEPLOYMENT_FILE_PATH
    printf "\n$YAML_SEPARATOR\n" >> $DEPLOYMENT_FILE_PATH
done

echo "Finsihed Building deployment.yaml"