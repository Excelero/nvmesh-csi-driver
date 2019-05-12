#!/usr/bin/env bash

export MANAGEMENT_SERVERS=$1
echo "run_tests.sh  MANAGEMENT_SERVERS=$MANAGEMENT_SERVERS"

python2 -m test.integration.run_all_tests

exit $?