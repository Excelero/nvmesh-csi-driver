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

# ssh tunnel for dashboard
ssh -L 8001:localhost:8001 n115
# command to expose dashboard from the machine
kubectl proxy --address='0.0.0.0' --port=8001 --accept-hosts='.*'
# dashboard url
localhost:8001/api/v1/namespaces/kube-system/services/https:kubernetes-dashboard:/proxy/

# fix permission error accesing docker daemon
# add to docker group
sudo usermod -a -G docker $USER

# get minikube docker-env
eval $(minikube docker-env)

# start a docker registry
docker run -d -p 5000:5000 --restart=always --name n115 registry:2

# get shell inside a container
kubectl exec -it <kube-pod> -c <kube-container> -- /bin/bash

# open feature-gates
apiServerExtraArgs:
  feature-gates: "ExpandCSIVolumes=true,ExpandInUsePersistentVolumes=true"
controllerManagerExtraArgs:
  feature-gates: "ExpandCSIVolumes=true,ExpandInUsePersistentVolumes=true"
schedulerExtraArgs:
  feature-gates: "ExpandCSIVolumes=true,ExpandInUsePersistentVolumes=true"