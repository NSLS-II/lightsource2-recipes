#!/bin/bash

set -e

./configure --prefix=$PREFIX \
    --enable-shared --enable-ipv6 \
    --with-tcltk-includes="-I$PREFIX/include" \
    --with-tcltk-libs="-L$PREFIX/lib -ltcl8.5 -ltk8.5" \
    CPPFLAGS="-I$PREFIX/include" \
    LDFLAGS="-L$PREFIX/lib -Wl,-rpath=$PREFIX/lib,--no-as-needed"

make -j$(getconf _NPROCESSORS_ONLN)
make install

ln -s python3 $PREFIX/bin/python
