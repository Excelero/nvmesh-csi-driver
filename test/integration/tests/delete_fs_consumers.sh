#!/usr/bin/env bash

source ./test_utils.sh

echo "Removing $num_of_volumes Consumers"

for ((i=1; i<=num_of_volumes; i++))
do
   echo "Removing Pod fs-consumer-$i"
   kubectl delete pod fs-consumer-$i
done

wait_for_pods_to_be_removed

exit 0
