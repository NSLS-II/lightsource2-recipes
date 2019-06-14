#!/bin/bash

USERNAME=$(id -u -n)
Xvfb :1 -screen 0 1280x1024x24 -auth localhost &
export DISPLAY=:1
$PYTHON setup.py install --single-version-externally-managed --record record.txt

unamestr=`uname`
if [ "$unamestr" != 'Darwin' ]; then 
	killall -u $USERNAME Xvfb 
fi
