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
        '--from-domain',
        nargs='?',
        help="anaconda api domain to mirror from. Only relevant if you are "
             "not using anaconda.org",
        default="https://api.anaconda.org"
    )
    p.add_argument(
        '--from-token',
        nargs="1",
        help=("anaconda token used to authenticate you to the given anaconda "
              "site. Required for uploading unless you are logged in (via "
              "`anaconda login`)"),
    )
    p.add_argument(
        '--to-owner',
        nargs='?',
        help=("anaconda user to mirror packages to. Also acceptable to "
              "pass in user/channel. channel will default to main unless "
              "explicitly provided")
    )
    p.add_argument(
        '--to-domain',
        nargs='?',
        help="anaconda api domain to mirror to. Only relevant if you are "
             "not using anaconda.org",
        default="https://api.anaconda.org"
    )
    p.add_argument(
        '--to-token',
        nargs="1",
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
    args.to_channel = 'main'
    args.from_channel = 'main'
    print(args)

    try:
        args.from_owner, args.from_channel = args.from_owner.split('/')
    except ValueError:
        # no extra channel information was passed
        pass
    try:
        args.to_owner, args.to_channel = args.to_owner.split('/')
    except ValueError:
        # no extra channel information was passed
        pass
    from_cli = binstar_client.Binstar(token=args.from_token,
                                      domain=args.from_domain)
    to_cli = binstar_client.Binstar(token=args.to_token,
                                    domain=args.to_domain)

    # Get the package metadata from the specified anaconda channel
    from_packages = from_cli.show_channel(args.from_channel,
                                               args.from_owner)
    from_files = [f['basename'] for f in from_packages['files']]
    if args.list:
        # print out the list of all files on the source channel and exit
        print("""
    Listing all files on {}/{}/{}
""".format(args.site, args.from_owner, args.from_channel))
        pprint(from_files)
        sys.exit(0)

    # Find the packages on the source channel that match the packages specified
    # on the command line
    matched = [f for f in from_files
                 for p in args.packages if p in f]
    # and print them out
    print("""
    Packages that match {} on {}/{}/{}
""".format(args.packages, args.from_domain, args.from_owner, args.from_channel))
    pprint(matched)

    # get the package metadata on the target channel
    packages_on_destination = to_cli.show_channel(args.to_channel, args.to_owner)
    files_on_destination = [f['basename']
                            for f in packages_on_destination['files']]
    # figure out which of these packages actually need to be copied
    to_copy = [f for f in matched if f not in files_on_destination]

    # print out the packages that need to be copied
    print("""
    Packages that match {} and do not already exist on {}/{}/{}
""".format(args.packages, args.to_domain, args.to_owner, args.to_channel))
    pprint(to_copy)

    if args.dry_run:
        # don't upload anything.  Print out why we are quitting and then quit
        print("""
    Exiting because --dry-run flag is set
""")
        sys.exit(0)

    # now grab the full file names, which anaconda upload needs.  This is the
    # 'spec' portion of the `anaconda upload` command
    # download_files =
    full_names = [f['full_name'] for f in from_packages['files']
                  if f['basename'] in to_copy]
    print("Actual package names to be uploaded")
    pprint(full_names)
    # loop over all packages that need to be copied
    for full_name in full_names:
        cmd = ['anaconda', 'copy',
               '--to-owner', args.to_owner,
               '--to-label', args.to_channel,
               full_name]

        printable_cmd = cmd
        if args.to_token is not None:
            # insert the token argument only if it exists. Also scrub it
            # for printing
            cmd.insert(1, args.to_token)
            cmd.insert(1, '--token')
            printable_cmd = cmd.copy()
            printable_cmd[2] = 'SCRUBBED_TOKEN'
        print('Upload command: {}'.format(' '.join(printable_cmd)))
        # actually do the upload
        stdout, stderr, returncode = Popen(cmd)
        # print(stdout)
        if returncode != 0:
            print("""
    stderr from {}
""".format(cmd))
            pprint(stderr)


if __name__ == "__main__":
    cli()
