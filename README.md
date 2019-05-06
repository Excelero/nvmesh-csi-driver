
# Excelero NVMesh - Container Storage Interface (CSI) Driver

##Version Info
Driver Version:     0.0.1

CSI spec version:   1.1.0

supported version of CSI in Kubernetes:
https://kubernetes-csi.github.io/docs/#kubernetes-releases

* Kubernetes 1.13 currently supports only CSI 1.0.0, but 1.1.0 only introduced Volume Expansion and did not change previous interface, and therefore has no 'breaking changes'.

##Build
Building the driver consists of few stages:
1. building the drivers docker image


##Deploy
NVMesh CSI driver is compatible with any Container Orchestration (CO) system that support the CSI spec.
Having said that, the deployment of CSI drivers is not covered in the spec, and so each CO can have a different way of deploying and registering the driver.

This section covers the deployment per CO system
 
#### Kubernetes
Deployment of NVMesh CSI driver consists of the following stages:

##### 1. Upload docker image to docker registry

upload the driver container image (nvmesh-csi-plugin) to a private docker registry deployed at your site, or to each nodes local docker registry

you can use the `build_tools/docker_build.sh` script to build the image with on hte current docker environment

##### 2. load resources to kubernetes

Run the following command using on a node with kubelet cli

    cd ./deploy
    ./deploy.sh

This will load a new 'nvmesh-csi' namespace, and the following resources:
secrets, configMaps, RBAC permissions, nvmesh-storage-classes

and will deploy and run the driver.

##### 3. Configuration

Go to Kubernetes Dashboard > `Config Maps` > `nvmesh-config`
and edit `management.servers` as needed

In case the Config Map `nvmesh-config` is not listed, make sure to select `Namespace` > `nvmesh-csi`



