#!/bin/bash

./Util/preconfig && \
./configure --prefix=$PREFIX --without-tcsetpgrp && \
make && \
make install.bin install.modules
