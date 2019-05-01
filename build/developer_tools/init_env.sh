#!/usr/bin/env bash

DEPL_DIR=../../deploy/kubernetes

kubectl create -f $DEPL_DIR/rbac-permissions.yaml
kubectl create -f $DEPL_DIR/nvmesh_secrets.yaml
kubectl create -f $DEPL_DIR/examples/create-nvmesh-storage-class.yaml