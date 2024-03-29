cd ../../../

registry=`cat deploy/kubernetes/helm/nvmesh-csi-driver/values-dev.yaml | yq '.dev.registry'`

if [ -z $registry ]; then
  registry=local:5000
fi

image_name="$registry/nvmesh-csi-test-tool:dev"

docker build -f test/integration/container/Dockerfile . --tag $image_name


# Create ConfigMap from test/config.yaml

config_map_file=test/integration/container/configmap.yaml
config_file_path=test/config.yaml

#kubectl create configmap --dry-run=client integration-test-config --from-file=$config_map_file --output yaml | tee $config_map_file

cat > $config_map_file <<- EOM
kind: ConfigMap 
apiVersion: v1 
metadata:
  name: integration-test-config
  labels:
    nvmehs-csi-testing: "" 
data:
  # This is the complete content of test/config.yaml
  config.yaml: | 
EOM

cat $config_file_path | sed 's/^/    /' >> $config_map_file
