#!/usr/bin/env bash

graceful_exit() {
    echo "exiting!"
    exit 0
}

trap graceful_exit SIGINT SIGTERM