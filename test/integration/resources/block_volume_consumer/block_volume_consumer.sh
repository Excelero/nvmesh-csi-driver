#!/usr/bin/env bash

VOLUME_PATH=/dev/my_block_dev

graceful_exit() {
    echo "Bye Bye!"
    exit 0
}

get_info() {
    lsblk

    ls -l /dev/

    cat /etc/mtab | grep $VOLUME_PATH

    df -h | grep $VOLUME_PATH
}

loop_forever() {
    while true
    do
        echo "I'm still here..."
        echo "---------------------------"
        sleep 2
    done
}

test_latency() {
    dd if=/dev/zero of=/dev/my_block_dev bs=1M count=100
    fio $VOLUME_PATH --direct=1 --rw=randrw --norandommap --randrepeat=0 --ioengine=libaio --rwmixread=100 --group_reporting --name=4ktestread --time_based --verify=0 --iodepth=1 --numjobs=1s --size=4k --bs=4k --runtime=30 --random_generator=tausworthe64
}

trap graceful_exit SIGINT SIGTERM

set -x
get_info
set +x

test_latency
loop_forever


echo "If this is printed, an error has occurred"