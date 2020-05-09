#!/bin/bash

python -m grpc_tools.protoc -Iproto --python_out=diagnosis-api/. --grpc_python_out=diagnosis-api/. proto/db19.proto
python -m grpc_tools.protoc -Iproto --python_out=simulate/. --grpc_python_out=simulate/. proto/db19.proto
