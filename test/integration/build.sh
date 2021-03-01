#!/usr/bin/env bash

docker build resources/fs_consumer/ --tag excelero/fs-consumer-test:develop
docker build resources/block_volume_consumer/ --tag excelero/block-consumer-test:develop
docker build resources/io_test/ --tag excelero/nvmesh-io-test:dev
