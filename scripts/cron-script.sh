#!/bin/bash
SCRIPT_PATH=/tmp/init-conda-build.sh
rm $SCRIPT_PATH
wget https://raw.githubusercontent.com/ericdill/conda-build-utils/master/scripts/init-for-conda-build.sh -O $SCRIPT_PATH
bash $SCRIPT_PATH
bash /tmp/$LOGNAME/dev-build
