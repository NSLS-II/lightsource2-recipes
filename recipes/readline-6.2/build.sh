#!/bin/bash

set -e

./configure --prefix=$PREFIX --with-curses
make -j$(getconf _NPROCESSORS_ONLN) SHLIB_LIBS="-ltinfo -L$PREFIX/lib"
make install

