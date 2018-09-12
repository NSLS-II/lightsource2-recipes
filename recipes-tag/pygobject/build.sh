#!/usr/bin/env bash

set -e

if [ -n "$OSX_ARCH" ] ; then
    export LDFLAGS="$LDFLAGS -Wl,-rpath,$PREFIX/lib"
fi

./configure --with-python=${PYTHON} --prefix="${PREFIX}"
make check TEST_NAMES=test_gi
make install

