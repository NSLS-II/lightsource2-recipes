#!/bin/bash

export EPICS_BASE=$PREFIX/epics
export EPICS_HOST_ARCH=linux-x86_64
$PYTHON setup.py build
$PYTHON setup.py install