#!/usr/bin/env bash

DATA_FILE=/tmp/data.txt
VOLUME_PATH=/dev/my_block_dev

graceful_exit() {
    echo "Bye Bye!"
    exit 0
}

get_info() {
    ls -l /dev/nvmesh/

    ls -l /mnt/

    cat /etc/mtab | grep $VOLUME_PATH

    df -h | grep $VOLUME_PATH
}

create_data_file() {
    DATA="Block Volume Test\nDate Created:$(date)\nHostname:$(hostname)"
    echo "Creating Data File at $DATA_FILE"
    echo "$DATA" > $DATA_FILE

    echo "Testing File Created:"
    cat $DATA_FILE
}

work_loop() {
    echo "Starting Work Loop"
    TEMP_FILE=/tmp/temp_file.txt
    DATA_SIZE
    while true
    do
        echo "Writing Data to Block Volume"
        dd if=$DATA_FILE of=$VOLUME_PATH

        echo "Reading first 40K from Block Volume into a file"
        dd if=$VOLUME_PATH of=$TEMP_FILE bs=4096 count=10

        echo "File Contents:"
        cat $TEMP_FILE

        echo "---------------------------"
        sleep 2
    done
}

trap graceful_exit SIGINT SIGTERM

set -x
get_info
set +x

create_data_file
work_loop

echo "If this is printed, an error has occurred"