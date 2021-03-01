#!/usr/bin/env bash

cd ../

python2 -m unittest discover test/sanity

exit $?