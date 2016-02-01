#!/bin/bash
wget https://raw.githubusercontent.com/ericdill/conda-build-utils/master/scripts/init-for-conda-build.sh -O /tmp/init-conda-build.sh
bash /tmp/init-conda-build.sh
bash ~/dev-build
