#!/bin/bash
export CPPFLAGS='-I $PREFIX/include'
${PYTHON} setup.py build
${PYTHON} setup.py install
