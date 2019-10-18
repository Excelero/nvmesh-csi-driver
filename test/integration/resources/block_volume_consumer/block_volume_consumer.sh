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

do_io() {
    fio $VOLUME_PATH --direct=1 --rw=randrw --norandommap --randrepeat=0 --ioengine=libaio --rwmixread=100 --group_reporting --name=4ktestread --time_based --verify=0 --iodepth=1 --numjobs=1s --size=$bs --bs=$bs --runtime=$run_time --random_generator=tausworthe64
}

run_io_tests() {
    # Run
    run_time=30

    bs=4k
    do_io

    bs=8k
    do_io

    bs=128k
    do_io

}

trap graceful_exit SIGINT SIGTERM

set -x
get_info
set +x

run_io_tests
loop_forever


echo "If this is printed, an error has occurred"