#!/bin/bash

from_token=`cat ~/dev/dotfiles/tokens/lightsource2-testing.token`
from_owner="conda-forge"
from_domain="https://api.anaconda.org"

to_token=`cat ~/dev/dotfiles/tokens/edill.anaconda.nsls2.token`
to_owner="edill"
to_domain="https://pergamon.cs.nsls2.local:8443/api"

conda-execute mirror.py conda-execute --from-token $from_token --from-owner $from_owner --from-domain $from_domain --to-token $to_token --to-owner $to_owner --to-domain $to_domain --platform linux-64 --to-disable-verify
