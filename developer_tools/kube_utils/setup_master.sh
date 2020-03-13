clear_old_files() {
    sudo rm -rf $HOME/.kube
    sudo rm -rf /etc/kubenretes
}


if [ "$1" == "reset"]; then
    sudo kubeadm reset
    clear_old_files
fi

# Install
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 > ~/kubeadm-init.log

# Setup config file
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Install Flannel - Node Networking Addon
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/2140ac876ef134e0ed5af15c65e414cf26827915/Documentation/kube-flannel.yml

# Install Dashboard
kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta8/aio/deploy/recommended.yaml

# show all pods in all namespaces
kubectl get pods --all-namespaces

# verify flannel and coredns are running

# edit dashborad service into NodePort so it will be available from every node on port 32414
kubectl patch svc kubernetes-dashboard -n kubernetes-dashboard -p '{"spec": {"type": "NodePort", "ports": [{ "nodePort": 32414,"port": 443,"protocol":"TCP","targetPort":8443 }]}}'

# Get Dashboard access
kubectl create serviceaccount dashboard-admin-sa
kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa

# Allow Dashboard to list namespaces

# Create cluster role that enables listing of namespaces
kubectl create -f - <<END
---
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
metadata:
  name: list-namespace
rules:
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["list"]
END

# create cluster role binding
kubectl create clusterrolebinding list-namespace-rule --clusterrole=list-namespace
kubectl patch clusterrolebinding list-namespace-rule -p '{"subjects": [{"kind": "ServiceAccount","name": "kubernetes-dashboard","namespace": "kubernetes-dashboard"}]}'

# Finish Info
echo "-------------------------------------"
echo "kubeadm init logs are at ~/kubeadm-init.log"
echo "Dashboard availabel at: localhost:32414"
echo "TOKEN:"
kubectl get secrets
echo "to get the toekn run: kubectl describe secret dashboard-admin-sa-token-????"
echo "get join command by running: "
echo "kubeadm token create --print-join-command"

kubeadm token create --print-join-command

