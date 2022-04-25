new_version=$1
new_numeric_version=$(echo $new_version | cut -d v -f2)


print_warning_message() {
    echo "Bumping version to $new_version"
    echo "This will:"
    echo -e "\t * update the version file"
    echo -e "\t * update the Chart.yaml file"
    echo -e "\t * re-generate relevant YAML files"
    echo -e "\t * create a new git commit with the changes"
    echo -e "\t * add a new git tag with the version name"
    echo -e "\nAre you sure you want to continue?"
}

prompt_to_continue() {
    echo "Do you wish to continue?"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) $1; break;;
            No ) exit;;
        esac
    done
}

update_helm_chart() {
    yq -i .version='"'${new_numeric_version}'"' ../deploy/kubernetes/helm/nvmesh-csi-driver/Chart.yaml
    yq -i .appVersion='"'${new_version}'"' ../deploy/kubernetes/helm/nvmesh-csi-driver/Chart.yaml
    echo "Chart.yaml updated with version=${new_numeric_version} and appVersion=${new_version}"
}

bump_version() {
    echo "Updating version file"
    echo "$new_version" > ../version

    echo "Re-Generating deployment YAML files"
    cd ../deploy/kubernetes/scripts/
    ./build_deployment_file.sh
    if [ $? -ne 0 ]; then
        echo "Error running ./build_deployment_file.sh"
        exit 1
    fi

    echo "Creating a new Version Commit"
    # cd back to repo dir
    cd ../../../
    git add deploy/kubernetes/deployment*.yaml
    git add deploy/kubernetes/helm/nvmesh-csi-driver/Chart.yaml
    git add version
    git commit -m "Bump version to $new_version"

    echo "Adding a new git tag $new_version"
    git tag -a "$new_version" -m "$new_version"
}

if [ -z "$new_version" ]; then
    echo "Usage: ./bump_version v1.0.2"
    exit 1
fi



print_warning_message
update_helm_chart
prompt_to_continue bump_version