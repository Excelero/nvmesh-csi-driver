#!/usr/bin/env bash

graceful_exit() {
    echo "exiting!"
    exit 0
}

trap graceful_exit SIGINT SIGTERM

if [ -z "$num_of_volumes" ]; then
    num_of_volumes=30
fi