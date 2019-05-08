#!/usr/bin/env bash

cd ../
# using the -f flag allows us to include files from a directory out of the 'context'
# we need it because the Dockerfile is in build dir and sources are in driver dir

# NOTE: building while the snx VPN is running could cause network issues that will fail building the image
docker build -f build_tools/nvmesh-csi-plugin.dockerfile . --tag excelero/nvmesh-csi-plugin:develop

if [ $? -ne 0 ]; then
    echo "Docker image build failed"
    exit 1
fi
