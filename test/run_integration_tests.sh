#!/usr/bin/env bash

cd ../

export TEST_CONFIG_PATH="test/config.yaml"
python2 -m unittest discover test/integration

exit $?