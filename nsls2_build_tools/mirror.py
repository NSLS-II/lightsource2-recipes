#!/usr/bin/env conda-execute
"""
CLI to mirror all files in a package from one conda channel to another

"""
# conda execute
# env:
#  - anaconda-client
#
# run_with: python
import os
from argparse import ArgumentParser
from pprint import pprint
import re
import sys
import subprocess

import binstar_client


def Popen(cmd):
    """Returns stdout and stderr

    Parameters
    ----------
    cmd : list
        List of strings to be sent to subprocess.Popen

    Returns
    -------
    stdout : """
    # capture the output with subprocess.Popen
    try:
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
    stdout, stderr = proc.communicate()
    if stdout:
        stdout = stdout.decode()
    if stderr:
        stderr = stderr.decode()
    return stdout, stderr, proc.returncode


def cli():
    p = ArgumentParser("Mirror packages from one channel to a different "
                       "channel for a given anaconda.org site with an "
                       "anaconda token. Note: will also work with "
                       "the BINSTAR_TOKEN environmental variable set or if "
                       "you have logged in to anaconda via the `anaconda "
                       "login` command built in to anaconda-client")
    p.add_argument(
        'packages',
        nargs='*',
        help="List of package names to mirror from one channel to another"
    )
    p.add_argument(
        '--list',
        action='store_true',
        help='List all the packages on --from-user and then exit'
    )

    p.add_argument(
        '--from-owner',
        nargs='?',
        help=("anaconda user to mirror packages from. Also acceptable to "
              "pass in user/channel. channel will default to main unless "
              "explicitly provided")
    )
    p.add_argument(
        '--to-owner',
        nargs='?',
        help=("anaconda user to mirror packages to. Also acceptable to "
              "pass in user/channel. channel will default to main unless "
              "explicitly provided")
    )
    p.add_argument(
        '--site',
        nargs='?',
        help="anaconda api site. only relevant if you are not using anaconda.org",
        default="https://api.anaconda.org"
    )
    p.add_argument(
        '--token',
        nargs="?",
        help=("anaconda token used to authenticate you to the given anaconda "
              "site. Required for uploading unless you are logged in (via "
              "`anaconda login`)"),
    )
    p.add_argument(
        '--dry-run',
        action='store_true',
        help=("Figure out which packages would be copied, print it out and "
              "then exit")
    )

    args = p.parse_args()
    args.to_label = 'main'
    args.from_label = 'main'
    print(args)

    if args.token is None:
        args.token = os.environ.get('BINSTAR_TOKEN')

    try:
        args.from_owner, args.from_label = args.from_owner.split('/')
    except ValueError:
        # no extra channel information was passed
        pass
    try:
        args.to_owner, args.to_label = args.to_owner.split('/')
    except ValueError:
        # no extra channel information was passed
        pass
    cli = binstar_client.utils.get_server_api(token=args.token, site=args.site)

    packages_on_source = cli.show_channel(args.from_label, args.from_owner)
    files_on_source = [f['full_name'] for f in packages_on_source['files']]
    if args.list:
        print("""
    Listing all files on {}/{}/{}
""".format(args.site, args.from_owner, args.from_label))
        pprint(files_on_source)
        sys.exit(0)

    matched = [f for f in files_on_source
                 for p in args.packages if p in f]
    print("""
    Packages that match {} on {}/{}/{}
""".format(args.packages, args.site, args.from_owner, args.from_label))
    pprint(matched)

    packages_on_destination = cli.show_channel(args.to_label, args.to_owner)
    files_on_destination = [f['full_name'] for f in packages_on_destination['files']]
    to_copy = [f for f in matched if f not in files_on_destination]

    print("""
    Packages that match {} and do not already exist on {}/{}/{}
""".format(args.packages, args.site, args.to_owner, args.to_label))
    pprint(to_copy)

    if args.dry_run:
        print("""
    Exiting because --dry-run flag is set
""")
        sys.exit(0)


    # spec = '{}/{}/{}'.format(args.from_owner, args.from_label, to_copy[0])
    for full_name in to_copy:
        cmd = ['anaconda', 'copy',
               '--to-owner', args.to_owner,
               '--to-label', args.to_label,
               full_name]
        print(' '.join(cmd))
        Popen(cmd)


if __name__ == "__main__":
    cli()
