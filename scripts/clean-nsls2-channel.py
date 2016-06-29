#!/usr/bin/env python
import binstar_client
from binstar_client import Binstar
from argparse import Namespace
import os
from pprint import pprint
# Fill in your binstar token here
token = 'ed-a09a18b1-8bce-4582-b02b-d43c27db57bd'
username = 'nsls2-tag'
site = 'https://pergamon.cs.nsls2.local:8443/api'

os.environ['REQUESTS_CA_BUNDLE']='/etc/certificates/ca_cs_nsls2_local.crt'
cli = binstar_client.utils.get_binstar(Namespace(token=token, site=site))

def get_names(username, channel='main'):
    return set([name['full_name'].split('/')[1] for name in cli.show_channel(channel, username)['files']])

names = get_names(username)

print("About to remove the following packages from the channel %s" % username)
pprint(names)

yes_or_no = input("Yes or No (Yy/Nn)")

if yes_or_no.lower() == 'y':
    for name in names:
        cli.remove_package(username, name)
    print("The %s channel now has these packages" % username)
    pprint(get_names(username))
else:
    print("Not removing these packages")
