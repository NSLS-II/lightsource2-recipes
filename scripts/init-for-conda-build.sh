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
  find ~/Downloads -iname *miniconda* -print | head -n 1 | xargs -I {} bash {} -b -p $CONDA_DIR
  # if conda dir still doesn't exist, download and install
  if [ ! -d "$CONDA_DIR" ]; then
    MC_PATH=~/Downloads/miniconda.sh
    echo Dowloading miniconda to $MC_PATH
    wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $MC_PATH
    bash "$MC_PATH" -b -p "$CONDA_DIR"
  fi
  echo "
RAMDISK_DIR=$RAMDISK_DIR
CONDA_DIR=$CONDA_DIR
CONDARC=$RAMDISKDIR/.condarc
PATH=$CONDA_DIR/bin:\$PATH
anaconda config --set url https://pergamon.cs.nsls2.local:8443/api" > ~/.condabuildrc
  echo "
channels:
 - nsls2-dev
 - nsls2
 - anaconda
always_yes: true
show_channel_urls: true" > "$RAMDISKDIR/.condarc"
fi

which conda

source ~/.condabuildrc

conda install conda-build anaconda-client --yes
