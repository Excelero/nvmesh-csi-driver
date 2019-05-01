#!/usr/bin/env bash

kubectl delete service nvmesh-csi-controller -n nvmesh-csi
kubectl delete serviceaccount nvmesh-csi -n nvmesh-csi

kubectl delete statefulsets nvmesh-csi-controller -n nvmesh-csi
kubectl delete pod nvmesh-csi-controller-0 -n nvmesh-csi
kubectl delete daemonset nvmesh-csi-node-driver -n nvmesh-csi
kubectl delete pod nvmesh-csi-node-driver -n nvmesh-csi
