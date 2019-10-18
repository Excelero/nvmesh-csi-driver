#!/usr/bin/env bash

source ./test_utils.sh


# 1. Create Objects
echo "Creating 2 Volumes and a Deployment"

kubectl create -f ../resources/migration/migration_deployment.yaml
wait_for_volumes 2
wait_for_pods 1

# 2. Set Node as not schedulable
NODE=$(kubectl get pods -o wide | awk '{print $7}' | tail -1)
echo "Tainting Node $NODE with NoSchedule"
kubectl taint nodes $NODE key1=value1:NoSchedule

# 3. Delete pod
POD_NAME=$(kubectl get pod -o name | tail -1)
echo "Deleting pod $POD_NAME"
kubectl delete "$POD_NAME"

echo "Waiting for pod to delete"
count_down 3
wait_for_pods 1

POD_NAME=$(kubectl get pod -o name | tail -1)
echo "Found new pod $POD_NAME"

# 4. Make Node Schedulable
echo "Removing Node $NODE taint"
kubectl taint nodes $NODE key1:NoSchedule-

# 5. Delete resources

delete_all_objects_of_type deployment
wait_for_pods_to_be_removed

delete_all_objects_of_type pvc
wait_for_volumes 0

echo "Migration test finished successfully"