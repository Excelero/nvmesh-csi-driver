#!/usr/bin/env bash

echo $(date) - Started

minikube stop
minikube delete
rm -rf ~/.minikube
minikube start
./init_env.sh
minikube dashboard &

echo $(date) - Finished
