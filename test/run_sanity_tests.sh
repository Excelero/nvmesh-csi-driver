#!/usr/bin/env bash

export MANAGEMENT_SERVERS=$1
echo "run_sanity_tests.sh  MANAGEMENT_SERVERS=$MANAGEMENT_SERVERS"

cd ../

python2 -m test.sanity.run_all_tests

exit $?