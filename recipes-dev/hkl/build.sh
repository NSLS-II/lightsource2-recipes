#! /bin/bash

set -e

test -d m4 || mkdir m4
gtkdocize || exit 1

export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"
export ACLOCAL_PATH="$PREFIX/share/aclocal"
aclocal --print-ac-dir

$PREFIX/bin/autoreconf -ivf
./configure --disable-gui --enable-introspection=yes --disable-hkl-doc --prefix=$PREFIX 
# || { cat config.log ; exit 1 ; }
make
make install
