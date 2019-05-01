#!/usr/bin/env bash


minikube stop
minikube delete
rm -rf ~/.minikube
minikube start
minikube dashboard &