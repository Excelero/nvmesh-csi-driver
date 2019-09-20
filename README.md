
# Excelero NVMesh - Container Storage Interface (CSI) Driver

## Version Info
Driver Version:     0.0.1
CSI spec version:   1.1.0

Supported version of CSI in Kubernetes:
[Kubernetes	CSI Spec Compatibility](https://kubernetes-csi.github.io/docs/#kubernetes-releases)

Supported Features in each Kubernetes Release:
[Kubernetes CSI Change Log](https://kubernetes-csi.github.io/docs/kubernetes-changelog.html#features-1)

## Notes
* Minimum Kubernetes Version 1.13
* Block Volume Feature requires Kubernetes 1.14 or higher

## Usage
NVMesh CSI driver is compatible with any Container Orchestration (CO) system that support the CSI spec.
The deployment of CSI drivers is not covered in the spec, and so each CO might have a different way of deploying, registering and configuring the driver.

This section covers the usage per CO system.

### Kubernetes

#### 1. Deployment
To deploy the driver in Kuberentes run the following command from a node with kubectl in your cluster
```
kubectl apply -f https://raw.githubusercontent.com/Excelero/nvmesh-csi-driver/master/deploy/kubernetes/deployment.yaml
```

#### 2. Configuration

* If you are using Kubernetes Dashboard make sure the selected namespace is `nvmesh-csi` in the side menu

1. Edit Management Server Address

Go to `Config Maps` > `nvmesh-config` OR from the terminal run:
```
kubectl edit configmap -n nvmesh-csi nvmesh-csi-config
```

Edit `management.servers` to your MANAGEMENT_SERVERS configuration

`management.servers: server-1.domain.com`

If you deployed NVMesh Management in a Container using [Excelero/nvmesh-mgmt-docker](https://github.com/Excelero/nvmesh-mgmt-docker) use:

`management.servers: "nvmesh-management-svc.nvmesh.svc.cluster.local:4001"`

2. Edit Username and Password to the Management Server
Go to `Secrets` > `nvmesh-credentials` OR from the terminal run:
```
kubectl edit secret -n nvmesh-csi nvmesh-credentials
```

Edit `username` and `password` to your management server credentials configuration
 * secret in Kubernetes must be in base64 format
 * for example use: `echo -n 'admin@excelero.com' | base64` and `echo -n 'admin' | base64` to get the username and passsword in base64
 * for more info visit: [Kubernetes Docs - Convert your secret data to a base-64 representation](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/#convert-your-secret-data-to-a-base-64-representation)


#### 3. Opening Kubernetes Feature Gates
* This stage is only required for Kubernetes versions 1.13 - 1.14

Depending on the Kubernetes version some `Feature Gates` might require to be turned on manually

The following Feature Gates are required:

    ExpandCSIVolumes=true
    ExpandInUsePersistentVolumes=true
    BlockVolume=true
    CSIBlockVolume=true

* the --feature-gates argument should be added to the following Kubernetes Components:
  * **apiserver**           (Kubernetes ConfigMap kubeadm-config or /etc/kubernetes/manifests/kube-apiserver.yaml)
  * **controller-manager**  (Kubernetes ConfigMap kubeadm-config or /etc/kubernetes/manifests/kube-controller-manager.yaml)
  * **scheduler**           (Kubernetes ConfigMap kubeadm-config or /etc/kubernetes/manifests/kube-scheduler.yaml)
  * **kubelet**             (kubernetes ConfigMag kublet-config-<version> or /etc/sysconfig/kubelet)
* example of feature-gates argument
`--feature-gates=ExpandCSIVolumes=true,ExpandInUsePersistentVolumes=true,BlockVolume=true,CSIBlockVolume=true`

#### 4. Kubernetes Examples

The driver deployment creates storage-classes that correspond to each of the NVMesh default VPGs.

The Following storage classes will appear under namespace "nvmesh-csi"
* nvmesh-concatenated
* nvmesh-raid0
* nvmesh-raid1
* nvmesh-raid10
* nvmesh-ec

Create a PersistentVolumeClaim of RAID1 type:
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nvmesh-raid1
  namespace: nvmesh-csi-testing
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 3Gi
storageClassName: nvmesh-raid1
```
* This will default to a FileSystem Volume with ext4


Create a Storage-Class for volumes with xfs FileSystem:
```
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: nvmesh-xfs-class
  namespace: nvmesh-csi-testing
provisioner: nvmesh-csi.excelero.com
allowVolumeExpansion: true
volumeBindingMode: Immediate
parameters:
  vpg: DEFAULT_CONCATENATED_VPG
  fsType: xfs
```

Create a volume from the xfs Storage-Class we just created:
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nvmesh-xfs-volume
  namespace: nvmesh-csi-testing
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 3Gi
  storageClassName: nvmesh-xfs-class
```

Create a Raw Block Volume (Kubernetes 1.14 or higher)
```
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Block
  volumeBindingMode: Immediate
  resources:
    requests:
      storage: 3Gi
  storageClassName: nvmesh-concatenated
```
Create A Pod that uses a Block Volume
```
apiVersion: v1
kind: Pod
metadata:
  name: block-volume-consumer-pod
  namespace: nvmesh-csi-testing
  labels:
    app: block-volume-consumer-test
spec:
  containers:
    - name: block-volume-consumer
      image: excelero/block-consumer-test:develop
      volumeDevices:
        - name: block-volume
          devicePath: /dev/my_block_dev
  volumes:
    - name: block-volume
      persistentVolumeClaim:
        claimName: block-pvc
```
* More usage examples are available under deploy/kubernetes/examples/

## Build The Image Locally

Upload the driver container image (nvmesh-csi-driver) to a private Docker registry deployed at your site, or to each nodes local Docker registry

From a machine with SSH access to all nodes run the following:
```
cd ./build_tools
./build.sh --servers node1 node2 node3
```
* where node1,node2,node3 are the Kubernetes Cluster server names including the master node


#### Kubernetes Examples

The driver deployment creates storage-classes that correspond to each of the NVMesh default VPGs.

The Following storage classes will appear under namespace "nvmesh-csi"
* nvmesh-concatenated
* nvmesh-raid0
* nvmesh-raid1
* nvmesh-raid10
* nvmesh-ec

Create a PersistentVolumeClaim of RAID1 type:

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: nvmesh-raid1
      namespace: nvmesh-csi-testing
    spec:
      accessModes:
        - ReadWriteMany
      resources:
        requests:
          storage: 3Gi
    storageClassName: nvmesh-raid1

* This will default to a FileSystem Volume with ext4


Create a Storage-Class for volumes with xfs FileSystem:

    kind: StorageClass
    apiVersion: storage.k8s.io/v1
    metadata:
      name: nvmesh-xfs-class
      namespace: nvmesh-csi-testing
    provisioner: nvmesh-csi.excelero.com
    allowVolumeExpansion: true
    volumeBindingMode: Immediate
    parameters:
      vpg: DEFAULT_CONCATENATED_VPG
      fsType: xfs


Create a volume from the xfs Storage-Class we just created:

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: nvmesh-xfs-volume
      namespace: nvmesh-csi-testing
    spec:
      accessModes:
        - ReadWriteMany
      resources:
        requests:
          storage: 3Gi
      storageClassName: nvmesh-xfs-class


Create a Raw Block Volume (Kubernetes 1.14 or higher)

    apiVersion: v1
    kind: PersistentVolumeClaim
    metadata:
      name: block-pvc
    spec:
      accessModes:
        - ReadWriteOnce
      volumeMode: Block
      volumeBindingMode: Immediate
      resources:
        requests:
          storage: 3Gi
      storageClassName: nvmesh-concatenated

Create A Pod that uses a Block Volume

    apiVersion: v1
    kind: Pod
    metadata:
      name: block-volume-consumer-pod
      namespace: nvmesh-csi-testing
      labels:
        app: block-volume-consumer-test
    spec:
      containers:
        - name: block-volume-consumer
          image: excelero/block-consumer-test:develop
          volumeDevices:
            - name: block-volume
              devicePath: /dev/my_block_dev
      volumes:
        - name: block-volume
          persistentVolumeClaim:
            claimName: block-pvc

* More usage examples are available under deploy/kubernetes/examples/