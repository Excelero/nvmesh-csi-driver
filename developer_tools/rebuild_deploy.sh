#!/usr/bin/env bash

### MAIN ###
############

./clear_old_deployment.sh

cd ../build_tools
./build.sh

cd ../deploy/kubernetes/scripts
./build_deployment_file.sh

cd ..
kubectl apply -f ./deployment.yaml

