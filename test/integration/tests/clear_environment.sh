#!/usr/bin/env bash

source ./test_utils.sh

echo "=============== Clearing testing environment ==============="

delete_all_objects_of_type daemonset
delete_all_objects_of_type deployment
delete_all_objects_of_type pod
delete_all_objects_of_type pvc

delete_all_storage_classes_except_default

kubectl delete namespace nvmesh-csi-testing
kubectl create namespace nvmesh-csi-testing

echo "=============== Finished clearing testing environment ==============="
