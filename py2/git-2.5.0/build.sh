#!/bin/bash

make configure
export CURLDIR=$PREFIX
./configure --prefix=$PREFIX
make all doc info
make install install-doc install-html install-info

cd $PREFIX
rm -rf lib lib64
rm -rf share/man
strip bin/* || echo
strip libexec/git-core/* || echo
