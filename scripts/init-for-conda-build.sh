#!/bin/bash

# make sure that the ramdisk_dir env var exists
# if not, default to ~/ramdisk
if [ "$RAMDISK_DIR" == "" ]; then
  RAMDISK_DIR="$HOME/ramdisk"
else
  echo "RAMDISK_DIR already exists at $RAMDISK_DIR"
fi

# if the ramdisk dir does not already exist, then create a ramdisk!
if [ ! -d "$RAMDISK_DIR" ]; then
  mkdir "$RAMDISK_DIR"
  chmod 777 "$RAMDISK_DIR"
  sudo mount -t tmpfs -o size=10G tmpfs "$RAMDISK_DIR"
fi

if [ "$CONDA_DIR" == "" ]; then
  CONDA_DIR="$RAMDISK_DIR/mc"
fi
if [ ! -d "$CONDA_DIR" ]; then
  # check and see if we have a miniconda bash script available
  MC_PATH=`find ~/Downloads -iname *miniconda* -print | head -n 1`
  # if not, download one
  if [ $MC_PATH == "" ]; then
    MC_PATH = ~/Downloads/miniconda.sh
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $MC_PATH
  fi
  bash "$MC_PATH" -b -p "$CONDA_DIR"
  echo "
  RAMDISK_DIR=$RAMDISK_DIR
  CONDA_DIR=$CONDA_DIR
  PATH="$CONDA_DIR/bin":\$PATH" > ~/.condabuildrc
fi

source ~/.condabuildrc
conda install conda-build anaconda-client --yes
