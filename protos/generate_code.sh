#!/usr/bin/env bash

PROTO_FILE=./csi.proto
GENERATED_FILES_DIR=../driver/generated

python -m grpc_tools.protoc -I./ --python_out=$GENERATED_FILES_DIR --grpc_python_out=$GENERATED_FILES_DIR ./$PROTO_FILE