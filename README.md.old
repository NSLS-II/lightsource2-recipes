# lightsource2-recipes
The recipes that are needed at nsls2 but are not on `conda-forge` yet.

Here is a
[link to the conda package version matching specifications](http://conda.pydata.org/docs/spec.html#package-match-specifications)
for convenience.

## lightsource2-recipes/scripts

### cron/bootstrapping scripts
These scripts are what I run as cron jobs on freyja.nsls2.bnl.gov to build our
stack and upload to anaconda.org/lightsource2-dev and anaconda.org/lightsource2-tag

Bootstrap | Description
--- | ---
`bootstrap-dev-build` | Execute this script after filling in your authentication tokens for Slack and anaconda.org and it will pull down the latest copy of this repo, build the dev recipes and upload to anaconda.org/lightsource2-dev. Uses `nsls2-dev-build.sh` and `build.py` under the hood.
`bootstrap-tag-build` | Execute this script after filling in your authentication tokens for Slack and anaconda.org and it will pull down the latest copy of this repo, build the tag recipes and upload to anaconda.org/lightsource2-tag. Uses `nsls2-dev-build.sh` and `build.py` under the hood.
`bootstrap-mirror` | Execute this script after filling in your authentication tokens for Slack and anaconda.org and it will pull down the latest copy of this repo and run the mirroring for `https://anaconda.org/conda-forge{conda-forge,lightsource2-dev,lightsource2-tag}` to `https://anaconda.nsls2.bnl.gov/{conda-forge,lightsource2-dev,lightsource2-tag}`

To use the bootstrap build scripts with cron every 15 minutes, your crontab should look like this on freyja:
```
$ crontab -l
*/15 * * * * bash ~/bootstrap-tag-build
*/15 * * * * bash ~/bootstrap-dev-build
```

To use the mirroring script with cron every 15 minutes, your crontab should look like this on bcart
```
$ crontab -l
*/15 * * * * bash ~/bootstrap-mirror > ~/mirrorcronlog 2>&1
```

### All other scripts

Script | Description
--- | ---
`build.py` | Generic builder script for building a folder full of recipes with a ton of command line options.  This is the main script that sits behind `nsls2-dev-build.sh` and `nsls2-tag-build.sh` and those scripts are how you should probably interact with `build.py`. There are tons of command-line arguments. Have a look at the `cli()` function in build.py for the exhaustive list. Or run `conda execute build.py --help`
`nsls2-dev-build.sh` | Script that is run as a cron job on `freyja.nsls2.bnl.gov` under the `lili` account. Is used inside of `bootstrap-dev-build`. See that bootstrap script for the proper invocation of `nsls2-dev-build.sh`
`nsls2-tag-build.sh` | Script that is run as a cron job on `freyja.nsls2.bnl.gov` under the `lili` account. Is used inside of `bootstrap-tag-build`. See that bootstrap script for the proper invocation of `nsls2-tag-build.sh`
`mirror.py` | Generic mirroring script that can go across anaconda servers.  There are tons of command line options.  See its usage in `mirror-to-nsls2.sh` for how it is properly localized to nsls2. This script is used to mirror packages from one owner to another. There are a number of command line arguments that can be used for full granular control of which owner on which anaconda server. Consider using this script with the `mirror-to-nsls2.sh` script that sets up the call for you. This script might be moved to its own repo on conda-forge, but that will come later. (probably much later)
`mirror-to-nsls2.sh` | Localization of `mirror.py` for nsls2. Invoke it with `OWNER=conda-forge FROM_TOKEN="anaconda.org token" TO_TOKEN="anaconda.nsls2.bnl.gov token" mirror-to-nsls2.sh`. Where `OWNER` is any channel on anaconda.org that you want to mirror internally. and {FROM,TO}_TOKEN are tokens that you need to generate.
`tail-dev-log` | Script that will tail the most recent build log for the dev builds. If this is placed in `/usr/bin/` on freyja.nsls2.bnl.gov, then you can do neat things like save the following in a script: `ssh freyja.nsls2.bnl.gov tail-dev-log` and you can have a one-liner that will let you view the most recent build script
`tail-tag-log` | Same as above, but for the tag logs

### anaconda channel management scripts

Script | Description
--- | ---
`use_nsls2_binstar.sh` | Script that switches your anaconda api url and condarc to have contents relevant for nsls2. This is particularly useful if you find yourself switching back and forth from nsls2 to anaconda.org
`use_public_anaconda.sh` | Script that switches your anaconda api url and condarc to have contents relevant for anaconda.org. This is particularly useful if you find yourself switching back and forth from nsls2 to anaconda.org
`clean-public-channel.py` | Invoke with `BINSTAR_TOKEN="your binstar token" CLEAN_CHANNEL="channel to clean" clean-public-channel.py`.  This will remove *all* packages from the CLEAN_CHANNEL variable, after asking you for confirmation first.  Uses the anaconda domain: https://api.anaconda.org
`clean-nsls2-channel.py` | Invoke the same as `clean-public-channel.py` and uses the nsls2 anaconda server instead of the public one. NOTE: This script has not been used in a while, so I'm not sure if it still works.

## Building the stack from scratch

Look at the `bootstrap-tag-build` script, fill in your tokens and execute that script.

Then look at the `bootstrap-dev-build` script, fill in your tokens and execute that script.  Then you will have the stack!


## Questions

### How do I add a new package?

#### To conda-forge

1. fork github.com/conda-forge/staged-recipes
1. checkout a new branch
1. add your recipe into the `recipes/` folder
1. make sure it builds locally with conda-build
1. open up a PR against conda-forge/staged-recipes

#### To this repo

**dev recipe**

1. Add to lightsource2-recipes/recipes-dev
1. `conda build <recipe>` locally so you know it works
1. commit and push to master
1. The cron jobs will pick it up the next time they run, build the new recipe
   and push to anaconda.org/lightsource2-dev

**tag recipe**

1. Add to lightsource2-recipes/recipes-tag
1. `conda build <recipe>` locally so you know it works
1. commit and push to master
1. The cron jobs will pick it up the next time they run, build the new recipe
   and push to anaconda.org/lightsource2-tag
1. Strongly consider moving the recipe to conda-forge because they are the true
   experts regarding conda recipes and can help you make your recipe better.
   As an added bonus, you might even get osx-64, win-32 and win-64 builds too!

**config recipe**
1. Edit the config yaml in lightsource2-recipes/recipes-config
1. Navigate to the recipes-config directory in the terminal
1. Execute the `regenerate.py` script: `conda execute regenerate.py` Note that
   `regenerate.py` auto-commits the changes to the git repo
1. Push to master.

### How do you debug a package that is failing to build?
Get help from the folks at conda-forge. There is a gitter at gitter.im/conda-forge/conda-forge.github.io
