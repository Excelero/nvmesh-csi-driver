#!/usr/bin/env bash

DEPL_DIR=resources

# Deploy Static Assets
kubectl create -f $DEPL_DIR/nvmesh-csi-namespace.yaml
kubectl create -f $DEPL_DIR/nvmesh-credentials.yaml
kubectl create -f $DEPL_DIR/nvmesh-configmaps.yaml
kubectl create -f $DEPL_DIR/rbac-permissions.yaml
kubectl create -f $DEPL_DIR/../examples/create-nvmesh-storage-classes.yaml

# this will load and run the driver pods and containers over the cluster
kubectl create -f $DEPL_DIR/nvmesh-csi-deployment.yaml