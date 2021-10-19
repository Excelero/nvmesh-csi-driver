# Usage Examples

## Run Locally:

```
docker run --net=host \
	-e TEST_NAME=test_block_volume \
	-e KUBECONFIG=/home/root/.kube/config \
	-v /home/gil/.kube/config:/home/root/.kube/config \
	-v /etc/resolv.conf:/etc/resolv.conf \
	excelero/nvmesh-csi-test-tool:0.0.1
```


# Run In cluster:

```
apiVersion: v1
Kind: Pod
...
```

