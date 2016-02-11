#!/bin/bash

./configure --prefix=$PREFIX \
    --without-debug --without-ada --without-manpages \
    --with-shared --disable-overwrite --with-termlib=tinfo \
    --with-normal 

make -j$(getconf _NPROCESSORS_ONLN)
make install
