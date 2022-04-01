
# Excelero NVMesh - Container Storage Interface (CSI) Driver


## Versions And Compatibility
Driver Version:     1.2.1

NVMesh Version:     2.2.0 or higher

Kubernetes Version: 1.17 or higher

## Kubernetes Quick Start

### Using helm
```
# Download the helm chart
wget https://github.com/Excelero/nvmesh-csi-driver/releases/download/v1.2.1/helm-chart.nvmesh-csi-driver-1.2.1.tgz

# Install
kubectl create namespace nvmesh-csi
helm install nvmesh-csi-driver ./helm-chart.nvmesh-csi-driver-1.2.1.tgz --namespace nvmesh-csi --set config.servers=<your.mgmt.server>:4000 --set config.protocol=https
```

### Using kubectl
To deploy the driver in Kubernetes simply run the following command from a node with kubectl in your cluster

```
kubectl create namespace nvmesh-csi
kubectl create -f https://raw.githubusercontent.com/Excelero/nvmesh-csi-driver/1.2.1/deploy/kubernetes/deployment.yaml
```

## Documentation
For the full documentation of NVMesh CSI Driver please visit: [NVMesh CSI Driver User Manual](https://www.excelero.com/nvmesh-csi-driver-guide/)