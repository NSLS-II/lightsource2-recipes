#!/bin/bash

set -e

# BNL_URL=https://pergamon.cs.nsls2.local:8443/api
# PUBLIC_URL=https://api.anaconda.org
#
# if [ ! $BNL == '' ]; then
#   URL=$BNL_URL
# else
#   URL=$PUBLIC_URL
# fi
# make sure that the ramdisk_dir env var exists
# if not, default to ~/ramdisk
if [ "$RAMDISK_DIR" == "" ]; then
  RAMDISK_DIR="/tmp/$LOGNAME/ramdisk"
  mkdir -p $RAMDISK_DIR
  echo "RAMDISK_DIR set to $RAMDISK_DIR"
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
fi
# add some setup/teardown scripts
mkdir -p $CONDA_DIR/etc/conda/activate.d
echo "source $RAMDISK_DIR/.condabuildrc
mkdir -p ~/.config/binstar
echo 'url: https://pergamon.cs.nsls2.local:8443/api' > ~/.config/binstar/config.yaml
" > $CONDA_DIR/etc/conda/activate.d/setup.sh
mkdir -p $CONDA_DIR/etc/conda/deactivate.d
echo "
unset RAMDISK_DIR
unset CONDA_DIR
unset CONDARC
source ~/.bashrc" > $CONDA_DIR/etc/conda/deactivate.d/teardown.sh
# set up a condabuildrc file
echo "
export RAMDISK_DIR=$RAMDISK_DIR
export CONDA_DIR=$CONDA_DIR
export CONDARC=$RAMDISK_DIR/.condarc
" > "$RAMDISK_DIR/.condabuildrc"
# set up a custom condarc for the ramdisk env
echo "
channels:
- https://pergamon.cs.nsls2.local:8443/conda/nsls2-dev
- https://pergamon.cs.nsls2.local:8443/conda/nsls2
- https://pergamon.cs.nsls2.local:8443/conda/anaconda
always_yes: true
show_channel_urls: true" > "$RAMDISK_DIR/.condarc"

echo "
#!/bin/bash
rm -rf /tmp/staged-recipes-dev
git clone https://github.com/NSLS-II/staged-recipes-dev /tmp/staged-recipes-dev
for dir in /tmp/staged-recipes-dev/recipes/*
do
    echo \$dir
    conda_cmd="conda-build \$dir --python=3.5"
    echo $conda_cmd
    \$conda_cmd && anaconda -t $BINSTAR_TOKEN upload -u nsls2-dev \`\$conda_cmd --output\`
done
" > $RAMDISK_DIR/dev-build.sh

echo "
#!/bin/bash
source activate $CONDA_DIR
bash $RAMDISK_DIR/dev-build.sh" > ~/dev-build
chmod +x dev-build
# init the conda directory
source activate $CONDA_DIR
conda install anaconda-client conda-build