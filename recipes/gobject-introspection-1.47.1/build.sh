#! /bin/bash
# Copyright 2014-2015 Peter Williams and collaborators.
# This file is licensed under a 3-clause BSD license; see LICENSE.txt.

set -e
# don't get locally installed pkg-config entries:
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"
export PYTHON="$PREFIX/bin/python3.4"

# conda libffi doesn't come with pkgconfig info:
export FFI_CFLAGS="-I$PREFIX/include" FFI_LIBS="-L$PREFIX/lib"
./configure --prefix=$PREFIX --with-python=$PREFIX/bin/python3
make -j$(nproc --ignore=4)
make install

cd $PREFIX
# workaround for libffi .la file path issues
sed -i -e 's|lib/\.\./lib64|lib|g' lib/*.la lib/gobject-introspection/giscanner/*.la

# deal with env export
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d

ACTIVATE=$PREFIX/etc/conda/activate.d/gobject_introspection.sh
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/gobject_introspection.sh

GI_TYPELIB_PATH=$PREFIX/lib/girepository-1.0

# set up
echo "export GI_TYPELIB_PATH="$GI_TYPELIB_PATH >> $ACTIVATE

# tear down
echo "unset GI_TYPELIB_PATH" >> $DEACTIVATE

# clean up after self
unset ACTIVATE
unset DEACTIVATE
unset GI_TYPELIB_PATH
