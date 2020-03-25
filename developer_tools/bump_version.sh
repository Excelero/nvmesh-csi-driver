new_version=$1

print_warning_message() {
    echo "Bumping version to $new_version"
    echo "This will:"
    echo -e "\t * update the version file"
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

verify_helm_chart_updated() {
    app_version_in_helm_chart=$(cat ../deploy/kubernetes/helm/nvmesh-csi-driver/Chart.yaml | grep appVersion | cut -d ':' -f 2 | tr -d '[:space:]')
    if [ "$app_version_in_helm_chart" != "$new_version" ]; then
        echo "Error: helm Chart.yaml version ($app_version_in_helm_chart) not updated to the new version ($new_version)."
        echo "please go to deploy/kubernetes/helm/nvmesh-csi-driver/Chart.yaml and update the appVersion to the new version string"
        echo "NOTE: remember to increment both appVersion and the version (version of the chart)"
        exit 1
    fi
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
    git add version
    git commit -m "Bump version to $new_version"

    echo "Adding a new git tag $new_version"
    git tag -a "$new_version" -m "$new_version"
}

if [ -z "$new_version" ]; then
    echo "Usage: ./bump_version v1.0.2"
    exit 1
fi

verify_helm_chart_updated

print_warning_message
prompt_to_continue bump_version