About
-----
Master branch recipes for the NSLS-II software stack.  Blatently ripped from
https://github.com/conda-forge/staged-recipes.  Thanks @pelson!


Build status
------------

Linux builds: enabled --> status: [![Circle CI](https://circleci.com/gh/NSLS-II/staged-recipes-dev.svg?style=svg)](https://circleci.com/gh/NSLS-II/staged-recipes-dev)

Mac builds: disabled --> status: [![Build Status](https://travis-ci.org/nsls-ii/staged-recipes.svg?branch=master)](https://travis-ci.org/ericdill/staged-recipes)

Windows builds: disabled --> status: [![Build status](https://ci.appveyor.com/api/projects/status/47716ba4hkginhp2/branch/master?svg=true)](https://ci.appveyor.com/project/pelson/staged-recipes/branch/master)


Notes
-----
Need to set:
- UPLOAD_CHANNEL
- BINSTAR_TOKEN

Optional env vars:
- ANACONDA_SERVER_URL: defaults to "https://api.anaconda.org"

Building the dev stack internal to NSLS-II:
```bash
ANACONDA_SERVER_URL="https://pergamon.cs.nsls2.local:8443/api" UPLOAD_CHANNEL=nsls2-dev BINSTAR_TOKEN=your_token_here bash scripts/run_docker_build.sh
```

Building the dev stack external to NSLS-II:
```bash
UPLOAD_CHANNEL=nsls2-dev BINSTAR_TOKEN=your_token_here bash scripts/run_docker_build.sh
```
