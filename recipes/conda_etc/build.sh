#!/bin/bash

mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d

ACTIVATE=$PREFIX/etc/conda/activate.d/etc.sh
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/etc.sh
ETC=$PREFIX/etc

# set up
echo "export CONDA_ETC_="$ETC > $ACTIVATE

# tear down
echo "unset CONDA_ETC_" > $DEACTIVATE

# clean up after self
unset ACTIVATE
unset DEACTIVATE
unset ETC
