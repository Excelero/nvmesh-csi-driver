#!/usr/bin/env bash

print_help() {
    echo "Usage: ./copy_sources_to_machine.sh <hostname or ip> <hostname or ip> <hostname or ip>"
    echo "Example: ./copy_sources_to_machine.sh n115 n117 n127"
}

if [ -z $1 ]; then
    print_help
    exit 1
fi

# go to project root
for server in "$@"
do
    echo "Copying sources to $server.."
    rsync -r ../ $server:~/nvmesh-csi-driver/ &
    pids[${i}]=$!
done

# wait for all children
for pid in ${pids[*]}; do
    wait $pid
done

echo "Finished Copying sources to all machines"