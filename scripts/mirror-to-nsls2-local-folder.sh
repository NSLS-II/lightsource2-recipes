#!/bin/bash

# requires you to set the "OWNER" environmental variable
: ${FROM_OWNER?"Need to set FROM_OWNER"}
: ${FROM_TOKEN?"Need to set FROM_TOKEN"}
: ${TO_OWNER?"Need to set TO_OWNER"}
#: ${TO_TOKEN?"Need to set TO_TOKEN"}
: ${SLACK_TOKEN?"Need to set SLACK_TOKEN"}
: ${SLACK_CHANNEL?"Need to set SLACK_CHANNEL"}

# token from nsls2builder on anaconda.org
from_domain="https://api.anaconda.org"

# token from edill on anaconda.nsls2.bnl.gov
# to_domain="https://pergamon.cs.nsls2.local:8443/api"

LOGDIR=~/mirror-logs/`date +%Y`/`date +%m`/`date +%d`
mkdir -p $LOGDIR
LOGFILE="$LOGDIR/`date +%H.%M`-mirror-$TO_OWNER"

./mirror_local_folder.py --from-token $FROM_TOKEN --from-owner $FROM_OWNER --from-domain $from_domain --to-owner $TO_OWNER --platform linux-64 --log $LOGFILE --all --slack-token $SLACK_TOKEN --slack-channel $SLACK_CHANNEL

./mirror_local_folder.py --from-token $FROM_TOKEN --from-owner $FROM_OWNER --from-domain $from_domain --to-owner $TO_OWNER --platform noarch --log $LOGFILE --all --slack-token $SLACK_TOKEN --slack-channel $SLACK_CHANNEL
