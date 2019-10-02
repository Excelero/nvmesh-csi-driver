#!/bin/bash

tests=$(ls -l | grep -iv testbase | grep -E 'Test.*py$' | tr -s ' ' | cut -d' ' -f9)
echo "Running these files:"
echo ${tests}

pytest ${tests} --disable-warnings -vv 


