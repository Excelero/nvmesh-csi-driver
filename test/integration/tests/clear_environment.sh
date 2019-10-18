#!/usr/bin/env bash

source ./test_utils.sh

delete_all_objects_of_type daemonset
delete_all_objects_of_type deployment
delete_all_objects_of_type pod
delete_all_objects_of_type pvc

kubectl delete namespace nvmesh-csi-testing
kubectl create namespace nvmesh-csi-testing