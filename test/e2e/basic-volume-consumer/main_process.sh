#!/usr/bin/env bash

loop_forever() {
    echo "Looping Forever.."
    while true
    do
        sleep 60
    done
}

graceful_exit() {
    echo "Bye Bye!"
    exit 0
}

get_info() {
    ls -l /dev/nvmesh/

    ls -l /mnt/

    cat /etc/mtab | grep /mnt/vol

    df -h | grep /mnt/vol
}

work_loop() {
    echo "Starting Work Loop"
    while true
    do
        echo "`hostname`:$WORKER_ID: `date`" >> /mnt/vol/test-file
        cat /mnt/vol/test-file | tail -4
        echo "---------------------------"
        sleep 2
    done
}

trap graceful_exit SIGINT SIGTERM

set -x
get_info
set +x

work_loop

echo "If this is printed, an error has occurred"