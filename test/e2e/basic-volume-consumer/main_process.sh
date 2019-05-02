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

work() {
    ls -l /dev/nvmesh/

    ls -l /mnt/

    cat /etc/mtab | grep /mnt/vol

    df -h | grep /mnt/vol

    echo "my data" > /mnt/vol/test-file

    cat /mnt/vol/test-file

}

trap graceful_exit SIGINT SIGTERM

set -x
work
set +x

loop_forever



