# lightsource2-recipes
The recipes that are needed at nsls2 but are not on `conda-forge` yet.

## lightsource2-recipes/scripts

### cron/bootstrapping scripts
These scripts are what I run as cron jobs on freyja.nsls2.bnl.gov to build our
stack and upload to anaconda.org/lightsource2-dev and anaconda.org/lightsource2-tag

Bootstrap | Description
--- | ---
`bootstrap-dev-build` | Execute this script after filling in your authentication tokens for Slack and anaconda.org and it will pull down the latest copy of this repo, build the dev recipes and upload to anaconda.org/lightsource2-dev. Uses `nsls2-dev-build.sh` and `build.py` under the hood.
`bootstrap-tag-build` | Execute this script after filling in your authentication tokens for Slack and anaconda.org and it will pull down the latest copy of this repo, build the tag recipes and upload to anaconda.org/lightsource2-tag. Uses `nsls2-dev-build.sh` and `build.py` under the hood.

To use these scripts with cron, your crontab should look like this:
```
$ crontab -l
05 * * * * bash ~/bootstrap-tag-build
05 * * * * bash ~/bootstrap-dev-build
```

### All other scripts

Script | Description
--- | ---
`build.py` | Generic builder script for building a folder full of recipes with a ton of command line options.  This is the main script that sits behind `nsls2-dev-build.sh` and `nsls2-tag-build.sh` and those scripts are how you should probably interact with `build.py`. There are tons of command-line arguments. Have a look at the `cli()` function in build.py for the exhaustive list. Or run `conda execute build.py --help`
`nsls2-dev-build.sh` | Script that is run as a cron job on `freyja.nsls2.bnl.gov` under the `edill` account. Is used inside of `bootstrap-dev-build`. See that bootstrap script for the proper invocation of `nsls2-dev-build.sh`
`nsls2-tag-build.sh` | Script that is run as a cron job on `freyja.nsls2.bnl.gov` under the `edill` account. Is used inside of `bootstrap-tag-build`. See that bootstrap script for the proper invocation of `nsls2-tag-build.sh`
`mirror.py` | Generic mirroring script that can go across anaconda servers.  There are tons of command line options.  See its usage in `mirror-to-nsls2.sh` for how it is properly localized to nsls2. This script is used to mirror packages from one owner to another. There are a number of command line arguments that can be used for full granular control of which owner on which anaconda server. Consider using this script with the `do-mirror.sh` script that sets up the call for you. This script might be moved to its own repo on conda-forge, but that will come later. (probably much later)
`mirror-to-nsls2.sh` | Localization of `mirror.py` for nsls2.
`tail-dev-log` | Script that will ssh to freyja.nsls2.bnl.gov and tail the most recent dev build log
`tail-tag-log` | Script that will ssh to freyja.nsls2.bnl.gov and tail the most recent tag build log
### anaconda channel management scripts

Script | Description
--- | ---
`use_nsls2_binstar.sh` | Script that switches your anaconda api url and condarc to have contents relevant for nsls2. This is particularly useful if you find yourself switching back and forth from nsls2 to anaconda.org
`use_public_anaconda.sh` | Script that switches your anaconda api url and condarc to have contents relevant for anaconda.org. This is particularly useful if you find yourself switching back and forth from nsls2 to anaconda.org
`clean-public-channel.py` | Invoke with `BINSTAR_TOKEN="your binstar token" CLEAN_CHANNEL="channel to clean" clean-public-channel.py`.  This will remove *all* packages from the CLEAN_CHANNEL variable, after asking you for confirmation first.  Uses the anaconda domain: https://api.anaconda.org
`clean-nsls2-channel.py` | Invoke the same as `clean-public-channel.py` and uses the nsls2 anaconda server instead of the public one. NOTE: This script has not been used in a while, so I'm not sure if it still works.

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
