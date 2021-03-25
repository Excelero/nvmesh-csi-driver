
# Excelero NVMesh - Container Storage Interface (CSI) Driver


## Versions And Compatibility
Driver Version:     1.1.3

NVMesh Version:     2.0.5 or higher

CSI spec version:   1.3.0

Kubernetes Version: 1.17 or higher

## Kubernetes Quick Start

### Using helm
```
# Download the helm chart
wget https://github.com/Excelero/nvmesh-csi-driver/releases/download/v1.1.3/helm-chart.nvmesh-csi-driver-1.1.3.tgz

# Install
helm install nvmesh-csi-driver ./helm-chart.nvmesh-csi-driver-1.1.3.tgz --set config.servers=<your.mgmt.server>:4000 --set config.protocol=https
```

### Directly into Kubernetes (using kubectl)
To deploy the driver in Kubernetes simply run the following command from a node with kubectl in your cluster

```
kubectl apply -f https://raw.githubusercontent.com/Excelero/nvmesh-csi-driver/1.1.3/deploy/kubernetes/deployment.yaml
```

## Documentation
For the full documentation of NVMesh CSI Driver please visit: [NVMesh CSI Driver User Manual](https://www.excelero.com/nvmesh-csi-driver-guide/)