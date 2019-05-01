#!/usr/bin/env bash

graceful_exit() {
    echo "Bye Bye!"
    exit 0
}

trap graceful_exit SIGINT SIGTERM

echo "ls -l /dev/nvmesh/"
ls -l /dev/nvmesh/

echo "ls -l /mnt/"
ls -l /mnt/

echo "Looping Forever.."
while true
do
    sleep 60
done

