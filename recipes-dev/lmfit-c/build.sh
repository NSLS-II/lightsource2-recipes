#!/bin/bash
set -ex

mkdir build
cd build
cmake -G "$CMAKE_GENERATOR" \
	-DCMAKE_INSTALL_PREFIX="${PREFIX}" \
	-DCMAKE_BUILD_TYPE=Release $SRC_DIR
cmake --build .
cmake --build . --target install
