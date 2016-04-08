About
-----

This repo contains conda-recipes that are automatically built on circle-ci and uploaded to anaconda.org/lightsource2.


Build status
------------

Linux build status --> [![Circle CI](https://circleci.com/gh/NSLS-II/auto-build-tagged-recipes.svg?style=svg)](https://circleci.com/gh/NSLS-II/auto-build-tagged-recipes)

Mac build status (currently turned off) --> [![Build Status](https://travis-ci.org/nsls-ii/staged-recipes.svg?branch=master)](https://travis-ci.org/nsls-ii/staged-recipes)

Windows build status (currently turned off) --> [![Build status](https://ci.appveyor.com/api/projects/status/47716ba4hkginhp2/branch/master?svg=true)](https://ci.appveyor.com/project/pelson/staged-recipes/branch/master)


Building the stack from scratch
-------------------------------
1. copy xraylib from lightsource2 to whatever channel you want

    anaconda copy lightsource2/xraylib/3.1.0 --to-owner NEW_OWNER

2a. Modify the run_docker_build.sh script to change the upload_channel variable
    to be whatever you want it to be

2b. Run the docker build script in this repo

    BINSTAR_TOKEN=your_binstar_token bash scripts/run_docker_build.sh

3. Check your new channel

    anaconda show upload_channel
