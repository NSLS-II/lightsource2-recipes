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

# how_long="2 days ago"
how_long="2 hours ago"
last_updated="$(git log --pretty=format: --name-only --since="${how_long}" | grep recipes-tag/ | sort -u | cut -d/ -f2)"
echo "Last updated files since ${how_long}:"
echo "${last_updated}"
echo ""

len=$(echo "${last_updated}" | wc -l | awk '{print $1}')
for ((i=1; i<=len; i++)); do
    pkg_name=$(echo "${last_updated}" | head -${i} | tail -1)
    timestamp=$(date +%Y%m%d%H%M%S)
    container_name=${pkg_name}-${timestamp}

    echo "Package name: ${pkg_name}"
    echo "Running the docker container: ${container_name}"

    cat << EOF | docker run -i --rm \
                            -v $REPO_ROOT:/repo \
                            -a stdin -a stdout -a stderr \
                            --name ${container_name} \
                            $IMAGE_NAME \
                            bash || exit $?

echo "CONDARC_PATH=$CONDARC_PATH"

# Create the condarc that we need
echo "binstar_upload: false
always_yes: true
show_channel_urls: true
channels:
- $UPLOAD_CHANNEL
- anaconda
- conda-forge" > $CONDARC_PATH

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
echo "start installation"
conda install python=3.6 -y
conda install conda=4.3 conda-build=3.1 anaconda-client conda-execute conda-env


# not sure why this is here, but I'm reasonably certain it is important
export PYTHONUNBUFFERED=1

# execute the dev build
#./repo/scripts/build.py /repo/recipes-config -u $UPLOAD_CHANNEL --python 2.7 3.5 3.6 --numpy 1.11 1.12 1.13 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN --allow-failures
./repo/scripts/build.py /repo/recipes-tag/${pkg_name} -u $UPLOAD_CHANNEL --python 3.6 --numpy 1.14 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN  --allow-failures

echo "Ending time :"
date -u

EOF

done
