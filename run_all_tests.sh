#!/usr/bin/env bash

export CONFIG_FILE_PATH=$1
echo "run_all_tests.sh  CONFIG_FILE_PATH=$CONFIG_FILE_PATH"

python -m test.run_all_tests

exit $?