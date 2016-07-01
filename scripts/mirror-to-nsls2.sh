#!/bin/bash

# requires you to set the "OWNER" environmental variable
: ${OWNER?"Need to set OWNER"}
: ${FROM_TOKEN?"Need to set FROM_TOKEN"}
: ${TO_TOKEN?"Need to set TO_TOKEN"}

if [ -z ${SLACK_TOKEN+x} ]; then
  slack_arg="--slack-token $SLACK_TOKEN"
else
  slack_arg=""
fi;
echo slack_arg=$slack_arg
# token from nsls2builder on anaconda.org
from_domain="https://api.anaconda.org"

# token from edill on anaconda.nsls2.bnl.gov
to_domain="https://pergamon.cs.nsls2.local:8443/api"

LOGDIR=~/mirror-logs/`date +%Y`/`date +%m`/`date +%d`
mkdir -p $LOGDIR
LOGFILE="$LOGDIR/`date +%H.%M`-mirror-$OWNER"

./mirror.py --from-token $FROM_TOKEN --from-owner $OWNER --from-domain $from_domain --to-token $TO_TOKEN --to-owner $OWNER --to-domain $to_domain --platform linux-64 --to-disable-verify --log $LOGFILE --all $slack_arg
