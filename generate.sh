#!/bin/bash

python -m grpc_tools.protoc -Iproto --python_out=diagnosis-api/. --grpc_python_out=diagnosis-api/. proto/db19.proto
python -m grpc_tools.protoc -Iproto --python_out=usage/. --grpc_python_out=usage/. proto/db19.proto
