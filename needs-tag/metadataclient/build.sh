#!/bin/bash

sed -i 's|__CONDA_BUILD_PLACEHOLDER__|'$PREFIX'/etc|' metadataclient/conf.py

$PYTHON setup.py install --single-version-externally-managed --record=/dev/null

