#!/usr/bin/env bash

clear_old_install() {
        rm -rf /etc/kubernetes
        rm -rf /var/lib/kubelet/
        rm -rf /var/lib/etcd/
}

pre_install() {

        # - Disable SELinux
        setenforce 0
        sed -i --follow-symlinks 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux

        #- Enable br_netfilter Kernel Module
        modprobe br_netfilter
        echo '1' > /proc/sys/net/bridge/bridge-nf-call-iptables

        # - Disable SWAP
        swapoff -a

}

install() {
        # install dependencies
        yum install -y yum-utils device-mapper-persistent-data lvm2
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce


        #- Install Kubernetes
        cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=1
repo_gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg
        https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF

        yum install -y kubelet kubeadm kubectl

}

configure_dns() {

        cat <<EOF >> /etc/sysctl.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-arptables = 1
EOF

        sudo sysctl -p
        sudo iptables-save
}

clear_old_install
pre_install
install
configure_dns
