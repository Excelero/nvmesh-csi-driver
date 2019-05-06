#!/usr/bin/env bash

echo $(date) - Started

minikube stop
minikube delete
rm -rf ~/.minikube
minikube start
cd ../../deploy/kubernetes/
init_env.sh
minikube dashboard &

echo $(date) - Finished
