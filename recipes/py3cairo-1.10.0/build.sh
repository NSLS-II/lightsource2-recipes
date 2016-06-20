#! /bin/bash
# Copyright 2015 Peter Williams and collaborators.
# This file is licensed under a 3-clause BSD license; see LICENSE.txt.

set -e

cp $RECIPE_DIR/waf-1.8.16 waf
patch -p0 -i $RECIPE_DIR/01_wscript-1.8.16.patch

python waf --help >/dev/null # trigger unpacking of waflib directory

export CFLAGS=-I${PREFIX}/include/cairo
python waf configure --prefix=$PREFIX
python waf build
python waf install
