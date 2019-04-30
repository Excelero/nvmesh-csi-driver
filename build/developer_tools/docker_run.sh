#!/usr/bin/env bash

name="nvmesh-csi-plugin"
image="nvmesh-csi-plugin:latest"

docker run -i --net=host -v /etc/opt/NVMesh/:/conf/ -v /tmp/:/tmp/ -h $name --name $name --rm $image


