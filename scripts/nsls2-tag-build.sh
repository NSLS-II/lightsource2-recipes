#!/usr/bin/env bash

echo "Starting time :"
date -u

: ${BINSTAR_TOKEN?"Need to set BINSTAR_TOKEN"}
: ${SLACK_TOKEN?"Need to set SLACK_TOKEN"}
: ${SLACK_CHANNEL?"Need to set SLACK_CHANNEL"}
: ${UPLOAD_CHANNEL?"Need to set UPLOAD_CHANNEL"}
# Set up the environmental variables
# Set the path to the condarc
CONDARC_PATH="/opt/conda/.condarc"
# set the location of the repo
REPO_DIR="/repo"
# define the docker container to use
IMAGE_NAME="nsls2/debian-with-miniconda:v0.1.2"
# Set the channel to upload the built packages to
REPO_ROOT=$(cd "$(dirname "$0")/.."; pwd;)
docker pull $IMAGE_NAME

how_long="3 days ago"
last_updated="$(git log --pretty=format: --name-only --since="${how_long}" | grep recipes-tag/ | cut -d/ -f2 | sort -uR)"
echo "Last updated files since ${how_long}:"
echo ""
echo "${last_updated}"
echo ""

for pkg_name in ${last_updated}; do
    timestamp=$(date +%Y%m%d%H%M%S)
    container_name=${pkg_name}-${timestamp}

    echo "Package name: ${pkg_name}"
    echo "Running the docker container: ${container_name}"
    echo ""

    cat << EOF | docker run -i --rm \
                            -v $REPO_ROOT:$REPO_DIR \
                            -a stdin -a stdout -a stderr \
                            --name ${container_name} \
                            $IMAGE_NAME \
                            bash || exit $?

echo -e "==============================================================================="
echo -e "    Start of build: $pkg_name"
echo -e "==============================================================================="

/repo/scripts/build.py /repo/recipes-tag/${pkg_name} -u $UPLOAD_CHANNEL --python 3.6 3.7 --numpy 1.14 --token $BINSTAR_TOKEN --slack-channel $SLACK_CHANNEL --slack-token $SLACK_TOKEN  --allow-failures

echo "Ending time :"
date -u

echo -e "==============================================================================="
echo -e "    End of build: $pkg_name"
echo -e "==============================================================================="


EOF

done
