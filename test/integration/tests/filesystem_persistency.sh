#!/usr/bin/env bash

source ./test_utils.sh

echo "Testing FileSystem Persistency"

read -r -d '' create_volume_template << EOM
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-fs-persistency-test
  namespace: nvmesh-csi-testing
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 3Gi
  storageClassName: nvmesh-raid10
EOM

read -r -d '' pod << EOM
apiVersion: v1
kind: Pod
metadata:
  name: {{name}}
spec:
  containers:
    - name: {{name}}
      image: alpine
      command: ["/bin/sh", "-c", "{{cmd}}"]
      volumeMounts:
        - name: vol
          mountPath: /vol
  volumes:
    - name: vol
      persistentVolumeClaim:
        claimName: pvc-fs-persistency-test
EOM


echo "Creating FileSystem PVC"
echo "$create_volume_template" | kubectl create -f -
wait_for_pvc_to_bound pvc-fs-persistency-test

echo "Creating Pod to write to a file on the FileSystem"
pod_name=create-file-pod
data_to_write="Persistency Test"
cmd="echo \'$data_to_write\' > /vol/file1"
prepared_pod=$(echo "$pod" | sed -e "s|{{name}}|$pod_name|" | sed -e "s|{{cmd}}|$cmd|")
echo "Running pod: "
echo -e "$prepared_pod"
echo -e "$prepared_pod" | kubectl create -f -

wait_for_pod_status $pod_name Completed
kubectl delete pod $pod_name
wait_for_pods_to_be_removed

echo "Creating Job - Pod to read from the file"
pod_name=read-file-pod
cmd="cat /vol/file1"
echo "$pod" | sed -e "s|{{name}}|$pod_name|" | sed -e "s|{{cmd}}|$cmd|" | kubectl create -f -

wait_for_pod_status $pod_name Completed
# get output
output=$(kubectl logs $pod_name)

kubectl delete pod $pod_name
wait_for_pods_to_be_removed

echo "read output=$output"

if [ "$output" != "$data_to_write" ]; then
    echo "Error validating data, wrote \"$data_to_write\" but read \"$output\""
fi

echo "Remove PVC"
kubectl delete pvc pvc-fs-persistency-test

exit 0
