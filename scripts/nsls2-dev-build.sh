#!/usr/bin/env bash

echo "Starting time :"
date -u

: ${BINSTAR_TOKEN?"Need to set BINSTAR_TOKEN"}
: ${SLACK_TOKEN?"Need to set SLACK_TOKEN"}
: ${SLACK_CHANNEL?"Need to set SLACK_CHANNEL"}
: ${UPLOAD_CHANNEL?"Need to set UPLOAD_CHANNEL"}
# Set up the environmental variables
# Set the path to the condarc
CONDARC_PATH="/root/.condarc"
# set the location of the repo
REPO_DIR="/repo"
# define the docker container to use
IMAGE_NAME="nsls2/debian-with-miniconda:latest"
# Set the channel to upload the built packages to
REPO_ROOT=$(cd "$(dirname "$0")/.."; pwd;)
docker pull $IMAGE_NAME

echo "Running the docker container"

cat << EOF | docker run -i --rm \
                        -v $REPO_ROOT:/repo \
                        -a stdin -a stdout -a stderr \
                        $IMAGE_NAME \
                        bash || exit $?

echo "CONDARC_PATH=$CONDARC_PATH"

# Create the condarc that we need
echo "binstar_upload: false
always_yes: true
show_channel_urls: true
channels:
- $UPLOAD_CHANNEL
- lightsource2-tag
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

rm -rf /conda/pkgs  #magic line, needs to be figured out later

#conda install python=3.5 conda=4.1.12 -y 
#conda install conda-build=3.0 anaconda-client conda-execute conda-env=2.5.1
conda install python=3.6 -y
conda install conda=4.3 conda-build>=3.1 anaconda-client conda-execute conda-env


# not sure why this is here, but I'm reasonably certain it is important
export PYTHONUNBUFFERED=1

echo "repo contents: $repo"
ls /repo/recipes-dev

# execute the dev build
./repo/scripts/build.py /repo/recipes-dev -u $UPLOAD_CHANNEL --python 3.6 3.7 --numpy 1.14 --token $BINSTAR_TOKEN  --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN --allow-failures

echo "Ending time :"
date -u

EOF
