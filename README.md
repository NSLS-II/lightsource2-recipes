# conda-build-utils
Scripts that are generally useful in making `conda-build` a more friendly experience


# Instructions for building the master branch of our stack

1. log in to whatever machine you want to build the dev stack on

 - I am building on xf23id1-srv2. Thanks @stuwilkins!

2. sudo to root

 - `sudo su`

3. `wget https://raw.githubusercontent.com/ericdill/conda-build-utils/master/scripts/dev-build`

 - replace placeholder with your binstar token: `sed -i s/YOUR_BINSTAR_TOKEN_HERE/actual-binstar-token/g dev-build`

5. Edit the crontab
 - `EDITOR=vim crontab -e`
 - add this line: `0 * * * * ~/dev-build > /tmp/auto-dev-builds.sh`
 - protip: If you want to make sure it runs, replace the `0 *` with a minute
   or two in the future and the current hour, so if it is 10:04 AM, replace
   `0 *` with `5 10`

6. Profit.