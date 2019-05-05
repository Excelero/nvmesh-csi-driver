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
    rsync -r ../../ $server:~/projects/k8s_csi/
done
