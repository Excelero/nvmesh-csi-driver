#!/usr/bin/env bash

kubectl config set-context --current --namespace=nvmesh-csi

kubectl delete service nvmesh-csi-controller -n nvmesh-csi
kubectl delete serviceaccount nvmesh-csi -n nvmesh-csi

kubectl delete statefulsets nvmesh-csi-controller -n nvmesh-csi
kubectl delete pod nvmesh-csi-controller-0 -n nvmesh-csi --grace-period=3
kubectl delete daemonset nvmesh-csi-node-driver -n nvmesh-csi
kubectl delete pod nvmesh-csi-node-driver -n nvmesh-csi

kubectl delete pod nvmesh-volume-consumer --grace-period=0 --force -n nvmesh-csi

# Hints
# Delete Force:
# kubectl delete pod nvmesh-volume-consumer --grace-period=0 --force -n nvmesh-csi
