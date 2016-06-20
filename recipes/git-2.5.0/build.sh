#!/bin/bash

make configure
export CURLDIR=$PREFIX
# add  --without-tcltk  so that git-gui does not get built
./configure --prefix=$PREFIX --without-tcltk
make all
make install

cd $PREFIX
rm -rf lib lib64
rm -rf share/man
strip bin/* || echo
strip libexec/git-core/* || echo
