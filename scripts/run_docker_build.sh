#!/usr/bin/env bash

# NOTE: This script has been adapted from content generated by github.com/conda-forge/conda-smithy
CLONE_DIR=/tmp/$LOGNAME/staged-recipes-dev
USERNAME=lightsource2-dev

REPO_ROOT=$(cd "$(dirname "$0")/.."; pwd;)
IMAGE_NAME="ericdill/nsls2-builder:latest"

config=$(cat <<CONDARC

channels:
 - lightsource2-dev
 - lightsource2
 - conda-forge
 - defaults

always_yes: true
show_channel_urls: True
CONDARC
)

cat << EOF | docker run -i \
                        -v ${REPO_ROOT}/py2:/py2 \
                        -v ${REPO_ROOT}/py3:/py3 \
                        -v ${REPO_ROOT}/pyall:/pyall \
                        -a stdin -a stdout -a stderr \
                        $IMAGE_NAME \
                        bash || exit $?

if [ "${BINSTAR_TOKEN}" ];then
    export BINSTAR_TOKEN=${BINSTAR_TOKEN}
fi

echo USERNAME=$USERNAME
echo CLONE_DIR=$CLONE_DIR

# Unused, but needed by conda-build currently... :(
export CONDA_NPY='110'

export PYTHONUNBUFFERED=1
echo "$config" > ~/.condarc

# A lock sometimes occurs with incomplete builds. The lock file is stored in build_artefacts.
conda clean --lock
# conda install "pip<8.1"
# conda install conda-build conda-build-all --yes
# conda remove conda-build conda-build-all --yes
# pip uninstall --yes conda-build conda-build-all
# pip install https://github.com/conda/conda-build/zipball/master#egg=conda-build
# git clone https://github.com/ericdill/conda-build
# cd conda-build-all
# git checkout silence-git-errors
# python setup.py develop
# pip install https://github.com/conda/conda-build/zipball/master#egg=conda-build
pip install https://github.com/ericdill/conda-build-utils/zipball/master#egg=conda-build-utils
conda info

# allow failures on the conda-build commands
set -e
echo "========== Running py2 builds =========="
devbuild /py2 --username $USERNAME --pyver 2.7 --log $DEV_LOG.summary
echo "========== Running py3 builds =========="
devbuild /py3 --username $USERNAME --pyver 3.4 3.5 --log $DEV_LOG.summary
echo "========== Running pyall builds =========="
devbuild /pyall --username $USERNAME --pyver 2.7 3.4 3.5 --log $DEV_LOG.summary
# echo "
#
# ===== BUILDING PY2 =====
#
# "
# conda-build-all /py2-recipes --upload-channels lightsource2-dev --matrix-conditions "numpy >=1.10" "python >=2.7,<3" --inspect-channels lightsource2-dev
# echo "
#
# ===== BUILDING PY3 =====
#
# "
# conda-build-all /py3-recipes --upload-channels lightsource2-dev --matrix-conditions "numpy >=1.10" "python >=3.4" --inspect-channels lightsource2-dev
#
# echo "
#
# ===== BUILDING PY2&PY3 =====
#
# "
# conda-build-all /pyall-recipes --upload-channels lightsource2-dev --matrix-conditions "numpy >=1.10" "python >=2.7,<3|>=3.4" --inspect-channels lightsource2-dev

EOF
