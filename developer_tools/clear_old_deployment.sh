#!/usr/bin/env bash

kubectl config set-context --current --namespace=nvmesh-csi

kubectl delete service nvmesh-csi-controller
kubectl delete serviceaccount nvmesh-csi

kubectl delete statefulsets nvmesh-csi-controller
kubectl delete daemonset nvmesh-csi-node-driver

#kubectl delete pod nvmesh-csi-controller-0

kubectl delete daemonset multi-consumer-test

# Hints
# Delete Force:
# kubectl delete pod nvmesh-volume-consumer --grace-period=0 --force -n nvmesh-csi
