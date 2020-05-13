
# Excelero NVMesh - Container Storage Interface (CSI) Driver


## Versions And Compatibility
Driver Version:     1.0

CSI spec version:   1.1.0

Kubernetes Version: 1.13 or higher

## Kubernetes Quick Start

### Using helm
helm install nvmesh-csi-driver ./nvmesh-csi-driver --set config.servers=<your.mgmt.server>:4000 --set config.protocol=https

### Directly into Kubernetes (using kubectl)
To deploy the driver in Kuberentes simply run the following command from a node with kubectl in your cluster

```
kubectl apply -f https://raw.githubusercontent.com/Excelero/nvmesh-csi-driver/1.0/deploy/kubernetes/deployment-k8s-1.17.yaml
```

## Documentation
For the full documentation of NVMesh CSI Driver please visit: [NVMesh CSI Driver User Manual](https://www.excelero.com/nvmesh-csi-driver-guide/)