#!/usr/bin/env bash

# install dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v1.10.1/src/deploy/recommended/kubernetes-dashboard.yaml

# install dashboard container cluster monitoring and performance analysis
kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/heapster.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/influxdb/influxdb.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/heapster/master/deploy/kube-config/rbac/heapster-rbac.yaml


# get join node command (run on master)
sudo kubeadm token create --print-join-command

# get dashboard bearer token
kubectl get secret -n kube-system $(kubectl get serviceaccount -n kube-system kubernetes-dashboard -o jsonpath="{.secrets[0].name}") -o jsonpath="{.data.token}" | base64 --decode

# start the dashboard
kubectl proxy --accept-hosts='.*' --accept-paths='.*' --address 10.0.1.115

# ssh tunnel for dashboard
ssh -L 8001:localhost:8001 <user@server-ip>

# fix permission error accesing docker daemon
# add to docker group
sudo usermod -a -G docker $USER

# get minikube docker-env
eval $(minikube docker-env)

# start a docker registry
docker run -d -p 5000:5000 --restart=always --name n115 registry:2
