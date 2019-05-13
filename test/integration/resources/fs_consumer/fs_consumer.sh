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
    ls -lsa /mnt/

    cat /etc/mtab | grep /mnt/vol

    df -h /mnt/vol

    FS_SIZE=$(df -h /mnt/vol | tail -1 | awk '{ print $1 }')
    echo "File System Size: $FS_SIZE"
}

work_loop() {
    echo "Starting Work Loop"
    hostname=`hostname`
    while true
    do
        echo "$hostname:$WORKER_ID: `date`" >> /mnt/vol/$hostname-$WORKER_ID
        echo "List Files in /mnt/vol/:"
        ls -l /mnt/vol/

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