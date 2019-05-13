
# Excelero NVMesh - Container Storage Interface (CSI) Driver

## Version Info
Driver Version:     0.0.1
CSI spec version:   1.1.0

Supported version of CSI in Kubernetes:
[Kubernetes	CSI Spec Compatibility](https://kubernetes-csi.github.io/docs/#kubernetes-releases)

Supported Features in each Kubernetes Release:
[Kubernetes CSI Change Log](https://kubernetes-csi.github.io/docs/kubernetes-changelog.html#features-1)

## Notes
* Volume Expansion (CSI 1.1.0) is implemented but is not currently supported by Kubernetes (1.13)

## Deployment
NVMesh CSI driver is compatible with any Container Orchestration (CO) system that support the CSI spec.
Having said that, the deployment of CSI drivers is not covered in the spec, and so each CO might have a different way of deploying and registering the driver.

This section covers the deployment per CO system

#### Kubernetes
Deployment of NVMesh CSI driver consists of the following stages:

##### 1. Build & Upload Docker image

Upload the driver container image (nvmesh-csi-plugin) to a private Docker registry deployed at your site, or to each nodes local Docker registry

From a machine with SSH access to all nodes run the following:

    cd ./build_tools
    ./build.sh --servers node1 node2 node3

* where node1,node2,node3 are the Kubernetes Cluster server names including the master node

##### 2. Load resources & deploy driver

2.1 Run the following command on **one** node with kubectl cli

    # the sources will be in ~/nvmesh_csi_driver/ if you followed step 1
    cd ~/nvmesh_csi_driver/
    cd ./deploy
    ./deploy.sh

* This will load all resources and deploy the driver on the cluster.

resources include:
 * 'nvmesh-csi' namespace
 * secrets
 * configMaps
 * RBAC permissions
 * nvmesh storage classes

##### 3. Configuration

Using Dashboard:
3.1 make sure the selected namespace is `nvmesh-csi` in the side menu

3.2 Go to `Config Maps` > `nvmesh-config` and edit `management.servers` to your MANAGEMENT_SERVERS configuration

3.3 Go to `Secrets` > `nvmesh-credentials` and edit `username` and `password` to your management server credentials configuration
 * secret in Kubernetes must be in base64 format
 * for example use: `echo -n 'admin@excelero.com' | base64` and `echo -n 'admin' | base64` to get the username and passsword in base64
 * for more info visit: [Kubernetes Docs - Convert your secret data to a base-64 representation](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#convert-your-secret-data-to-a-base-64-representation)
