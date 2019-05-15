#!/usr/bin/env bash

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=30
fi

echo "Removing $num_of_volumes Consumers"

for ((i=1; i<=num_of_volumes; i++))
do
   echo "Removing Pod fs-consumer-$i"
   kubectl delete pod fs-consumer-$i
done

echo "waiting for all pods to be removed..."
get_pods() {
    pods=$(kubectl get pods -o name | wc -l)
}

get_pods
while [ "$pods" != 0 ];
do
    sleep 2
    echo "Waiting for $pods to delete"
    get_pods
done
echo "all pods are removed..."

exit 0
