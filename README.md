# nsls2-recipes
The recipes that are needed at nsls2 but are not on `conda-forge` yet.

## Mirroring channels `scripts/mirror.py`
This script is used to mirror packages from one owner to another. There are
a number of command line arguments that can be used for full granular control
of which owner on which anaconda server. Consider using this script with the
`scripts/do-mirror.sh` script that sets up the call for you.
## Building the stack from scratch

### If you can see `anaconda.org`

Navigate to the root of this git repository.
Decide what channel you want to upload to, `UPLOAD_CHANNEL`.
Have your anaconda token ready, `BINSTAR_TOKEN`.
Invoke the build script.

```
export BINSTAR_TOKEN=your_binstar_token
export UPLOAD_CHANNEL=lightsource2-tag
bash scripts/run_docker_build.sh
```

or, as a one-liner
```
BINSTAR_TOKEN=your_binstar_token UPLOAD_CHANNEL=lightsource2-tag bash scripts/run_docker_build.sh
```


### If you are at nsls2 and can see `anaconda.nsls2.bnl.gov`

Navigate to the root of this git repository.
Decide what channel you want to upload to, `UPLOAD_CHANNEL`.
Have your anaconda token ready, `BINSTAR_TOKEN`.
Get the current url of anaconda.nsls2.bnl.gov for uploading, `ANACONDA_SERVER_URL`
Invoke the build script.

```
export ANACONDA_SERVER_URL="https://pergamon.cs.nsls2.local:8443/api"
export BINSTAR_TOKEN=your_binstar_token
export UPLOAD_CHANNEL=lightsource2-tag
bash scripts/run_docker_build.sh
```

or, as a one-liner
```
ANACONDA_SERVER_URL="https://pergamon.cs.nsls2.local:8443/api" BINSTAR_TOKEN=your_binstar_token UPLOAD_CHANNEL=lightsource2-tag bash scripts/run_docker_build.sh
```


## Set up with crontab

Edit the crontab
```
EDITOR=vim crontab -e
```

add this line to run scripts every two hours
```
0 * * * * bash ~/path/to/nsls2-recipes/scripts/nsls2-tag-build.sh > /tmp/auto-dev-builds.sh
```

protip: If you want to make sure it runs, replace the `0 *` with a minute or
two in the future and the current hour, so if it is 10:04 AM, replace
`0 *` with `5 10`
