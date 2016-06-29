#!/bin/bash

# requires you to set the "FROM_OWNER" and "TO_OWNER" flags
: ${FROM_OWNER?"Need to set FROM_OWNER"}
: ${TO_OWNER?"Need to set TO_OWNER"}

from_token=`cat ~/dev/dotfiles/tokens/lightsource2-testing.token`
from_domain="https://api.anaconda.org"

# to_token=`cat ~/dev/dotfiles/tokens/edill.anaconda.nsls2.token`
to_token=`cat /home/edill/dev/dotfiles/tokens/edill.anaconda.nsls2.token`
to_domain="https://pergamon.cs.nsls2.local/api:8443"

LOGDIR=/home/$LOGNAME/mirror-logs/`date +%Y`/`date +%m`/`date +%d`
mkdir -p $LOGDIR
LOGFILE="$LOGDIR/mirror-`date +%H.%M`"

./mirror.py conda-execute --from-token $from_token --from-owner $FROM_OWNER --from-domain $from_domain --to-token $to_token --to-owner $TO_OWNER --to-domain $to_domain --platform linux-64 --to-disable-verify --log $LOGFILE
