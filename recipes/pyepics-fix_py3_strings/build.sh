#!/bin/bash
export PYEPICS_LIBCA=$PREFIX/lib/libca.so
echo Using LIBCA from $PYEPICS_LIBCA
${PYTHON} setup.py build
${PYTHON} setup.py install
