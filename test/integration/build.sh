#!/usr/bin/env bash

docker build containers/fs_consumer/ --tag excelero/fs-consumer-test:develop
docker build containers/block_volume_consumer/ --tag excelero/block-volume-consumer-test:develop
