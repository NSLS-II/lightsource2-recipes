#!/usr/bin/env bash

: ${BINSTAR_TOKEN?"Need to set BINSTAR_TOKEN"}
: ${SLACK_TOKEN?"Need to set SLACK_TOKEN"}
: ${SLACK_CHANNEL?"Need to set SLACK_CHANNEL"}
: ${UPLOAD_CHANNEL?"Need to set UPLOAD_CHANNEL"}
# Set up the environmental variables
# Set the path to the condarc
CONDARC_PATH="$HOME/.condarc"
# set the location of the repo
REPO_DIR="/repo"

echo "CONDARC_PATH=$CONDARC_PATH"

# Create the condarc that we need
echo "binstar_upload: false
always_yes: true
show_channel_urls: true
channels:
- $UPLOAD_CHANNEL
- anaconda" > $CONDARC_PATH

# And set the correct environmental variable that lets us use it
echo "Exporting CONDARC=$CONDARC_PATH"
export CONDARC=$CONDARC_PATH

# show the conda info and make sure that the $CONDARC_PATH is what is shown
# under "config file:" in the output of "conda info"
echo "showing conda info"
conda info

# show the contents of the condarc
echo "contents of condarc at $CONDARC_PATH"
cat $CONDARC_PATH

# install some required dependencies
#echo "start installation"
#conda install conda-build=2.0 anaconda-client conda-execute conda-env=2.5.1


# not sure why this is here, but I'm reasonably certain it is important
export PYTHONUNBUFFERED=1

# execute the dev build
#./repo/scripts/build.py /repo/recipes-config -u $UPLOAD_CHANNEL --python 2.7 3.5 3.6 --numpy 1.10 1.11 1.12 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN --allow-failures
#./repo/scripts/build.py /repo/recipes-tag -u $UPLOAD_CHANNEL --python 2.7 3.5 3.6 --numpy 1.10 1.11 1.12 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN  --allow-failures
#python build.py ../recipes-config -u $UPLOAD_CHANNEL --python 2.7 3.5 3.6 --numpy 1.10 1.11 1.12 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN --allow-failures
python build.py ../recipes-tag -u $UPLOAD_CHANNEL --python 2.7 3.6 --numpy 1.14 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN  --allow-failures


EOF
