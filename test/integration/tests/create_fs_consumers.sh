#!/usr/bin/env bash

source ./test_utils.sh

read -r -d '' create_consumer_template << EOM
apiVersion: v1
kind: Pod
metadata:
  name: fs-consumer-{index}
  namespace: nvmesh-csi-testing
  labels:
    app: fs-consumer-test
spec:
  containers:
    - name: fs-consumer-{index}
      image: excelero/fs-consumer-test:develop
      volumeMounts:
        - name: fs-volume
          mountPath: /mnt/vol/
  volumes:
    - name: fs-volume
      persistentVolumeClaim:
        claimName: vol-{index}
EOM

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=30
fi

echo "Creating $num_of_volumes Consumers"

for ((i=1; i<=num_of_volumes; i++))
do
   echo "Creating Pod fs-consumer-$i"
   echo "$create_consumer_template" | sed -e "s/{index}/$i/" | kubectl create -f -
done

echo "waiting for all pods to be running..."
get_running_pods() {
    ready_pods=$(kubectl get pods | grep Running | wc -l)
}

get_running_pods
while [ "$ready_pods" != "$num_of_volumes" ];
do
    sleep 2
    get_running_pods
    echo "Ready Pods: $ready_pods/$num_of_volumes"
done
echo "all pods are running..."

exit 0
