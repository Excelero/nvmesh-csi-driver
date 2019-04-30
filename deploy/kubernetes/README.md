
## Deploying in Kuberenetes:
In Order to deploy the NVMesh CSI driver:
1. Create and load username and password secrets file. (refer to [Creating Secrets Section](#creating_secrets))
2. Edit the MANAGEMENT_SERVERS env in ./csi-nvmesh-deployment.yaml, for example:
~~~~
 - name: MANAGEMENT_SERVERS
   value: "localhost:4000, nvme115:4000"
~~~~
3. Create Kubernetes Deployment using the kubectl CLI

`kubectl create -f ./csi-nvmesh-deployment.yaml`

<a name="creating_secrets"></a>
## Creating Secrets:
Kubernetes Secrets Documentation: 
https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/

####Quick Guide:

1. Convert your username and password into base64:

`echo -n 'admin@excelero.com' | base64`

`echo -n 'admin' | base64`

2. Put the values into the nvmesh_secrets.yaml file in the data section

3. Load the secrets into Kubernetes:

`kubectl kubectl apply -f ./nvmesh_secrets.yaml`