#!/usr/bin/env bash

DEPL_DIR=resources

# Deploy Static Assets
kubectl create -f $DEPL_DIR/nvmesh-csi-namespace.json
kubectl create -f $DEPL_DIR/nvmesh-secrets.yaml
kubectl create -f $DEPL_DIR/nvmesh-configmaps.yaml
kubectl create -f $DEPL_DIR/rbac-permissions.yaml
kubectl create -f $DEPL_DIR/examples/create-nvmesh-storage-class.yaml

# this will load and run the driver pods and containers over the cluster
kubectl create -f $DEPL_DIR/nvmesh-csi-deployment.yaml