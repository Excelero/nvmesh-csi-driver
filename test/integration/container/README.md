# Usage Examples

## Run Locally:

```
docker run --net=host \
	-e KUBECONFIG=/home/root/.kube/config \
	-v ~/.kube/config:/home/root/.kube/config \
	-v /etc/resolv.conf:/etc/resolv.conf \
	-v ~/projects/k8s-csi-driver/test/config.yaml:/config/config.yaml.read-only \
	nvme115:30500/nvmesh-csi-test-tool:dev
```


# Run In cluster:

```
apiVersion: v1
Kind: Pod
...
```

