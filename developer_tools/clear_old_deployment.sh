#!/usr/bin/env bash

../deploy/kubernetes/remove_deployment.sh

# remove all testing workloads
kubectl delete daemonset multi-consumer-test -n nvmesh-csi

# Hints
# Delete Force:
# kubectl delete pod nvmesh-volume-consumer --grace-period=0 --force -n nvmesh-csi
