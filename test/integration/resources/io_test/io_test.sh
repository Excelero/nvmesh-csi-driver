#!/usr/bin/env bash


graceful_exit() {
    echo "Exiting.."
    exit 0
}

log_header() {
    echo "-----------------------------------"
    echo $1
    echo "-----------------------------------"
}

get_info() {
    log_header "lsblk"
    lsblk

}

loop_forever() {
    echo "Done. waiting for SIGTERM"
    while true
    do
        sleep 60 &
        wait $!
    done
}

do_block_io() {
    log_header "running fio --direct=1 --rw=randrw --norandommap --randrepeat=0 --ioengine=libaio --rwmixread=100 --group_reporting --name=$bs"testread" --time_based --verify=0 --iodepth=1 --numjobs=1s --size=$bs --bs=$bs --runtime=$run_time --random_generator=tausworthe64 --filename=$VOLUME_PATH"
    fio --direct=1 --rw=randrw --norandommap --randrepeat=0 --ioengine=libaio --rwmixread=100 --group_reporting --name=$bs"testread" --time_based --verify=0 --iodepth=1 --numjobs=1s --size=$bs --bs=$bs --runtime=$run_time --random_generator=tausworthe64 --filename=$VOLUME_PATH
}

run_block_device_tests() {
    run_time=$RUN_TIME

    bs=4k
    do_block_io

    bs=8k
    do_block_io

    bs=128k
    do_block_io

}

run_fs_tests() {
    echo "Running Filesystem tests"
    echo "running /opt/iozone/bin/iozone $VOLUME_PATH -a"
    /opt/iozone/bin/iozone "$VOLUME_PATH" -a
}

verfiy_env_var_arguments() {
    if [ -z "$VOLUME_PATH" ]; then
        echo "Error: environment variable VOLUME_PATH not set. Please supply the path to the block device as env var VOLUME_PATH"
    fi

    if [ -z "$VOLUME_TYPE" ]; then
        echo "Error: environment variable VOLUME_TYPE not set. Expected \"Filesystem\" OR \"Block\""
    else
        if [ "$VOLUME_TYPE" != "Filesystem" ] && [ "$VOLUME_TYPE" != "Block" ]; then
            echo "Error: Unknown VOLUME_TYPE of \"$VOLUME_TYPE\". Expected \"Filesystem\" OR \"Block\""
        fi
    fi

    if [ -z "$RUN_TIME" ]; then
        RUN_TIME=30
    fi

    if [ ! -z "$EXIT_ON_FINISH" ] && [ "$EXIT_ON_FINISH" != "Yes" ]; then
        echo "Error: Unknown EXIT_ON_FINISH of \"$EXIT_ON_FINISH\". Expected value \"Yes\" or \"No\". Defaults to \"No\""
    fi
}

print_arguments() {
    echo "VOLUME_PATH=$VOLUME_PATH"
    echo "RUN_TIME=$RUN_TIME"
}

#######   Main   ######

trap graceful_exit SIGINT SIGTERM

verfiy_env_var_arguments

print_arguments

get_info

if [ "$VOLUME_TYPE" == "Filesystem" ]; then
    run_fs_tests
elif [ "$VOLUME_TYPE" == "Block" ]; then
    run_block_device_tests
fi

if [ "$EXIT_ON_FINISH" != "Yes" ]; then
    loop_forever
fi
