#!/bin/bash

./Util/preconfig && \
./configure --prefix=$PREFIX && \
make && \
make install.bin install.modules
