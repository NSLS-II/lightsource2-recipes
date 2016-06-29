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
import tempfile

import binstar_client


def Popen(cmd, *args, **kwargs):
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
        proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, *args, **kwargs)
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
        '--all',
        action='store_true',
        help=("Supercedes `packages` argument. Mirror *all* of the packages "
              "from `from-owner` to `to-owner`."),
        default=False
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
        nargs='?',
        help=("anaconda token used to authenticate you to the given anaconda "
              "site. Required for uploading unless you are logged in (via "
              "`anaconda login`)"),
    )
    p.add_argument(
        '--from-disable-verify',
        action='store_false',
        help=('ssl verify connection to the `from_site`'),
        default=True
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
        nargs='?',
        help=("anaconda token used to authenticate you to the given anaconda "
              "site. Required for uploading unless you are logged in (via "
              "`anaconda login`)"),
    )
    p.add_argument(
        '--to-disable-verify',
        action='store_false',
        help=('ssl verify connection to the `from_site`'),
        default=True
    )
    p.add_argument(
        '--dry-run',
        action='store_true',
        help=("Figure out which packages would be copied, print it out and "
              "then exit")
    )
    p.add_argument(
        '--platform',
        nargs="*",
        action="store",
        help=("Only copy packages for the listed platforms. Options are "
              "'osx-32', 'osx-64', 'linux-32', 'linux-64', 'win-32' and "
              "'win-64'.  Defaults to 'linux-64'"),
        default=["linux-64"]
    )

    args = p.parse_args()
    args.to_channel = 'main'
    args.from_channel = 'main'

    print("\nSummary"
          "\n-------")
    print("Mirroring from", args.from_owner, "at", args.from_domain)
    print("Mirroring to", args.to_owner, "at", args.to_domain)
    print("\nPlatforms"
          "\n---------")
    pprint(args.platform)
    print("\nPackages list"
          "\n-------------")
    if args.all:
        print("**all packages**")
    else:
        pprint(args.packages)
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
                                      domain=args.from_domain,
                                      verify=args.from_disable_verify)
    to_cli = binstar_client.Binstar(token=args.to_token,
                                    domain=args.to_domain, 
                                    verify=args.to_disable_verify)

    # Get the package metadata from the specified anaconda channel
    from_packages = from_cli.show_channel(args.from_channel,
                                          args.from_owner)
    from_files = {f['basename']: f for f in from_packages['files'] 
                  if f['attrs']['subdir'] in args.platform}
    if args.list:
        # print out the list of all files on the source channel and exit
        print("""
    Listing all files on {}/{}/{}
""".format(args.from_domain, args.from_owner, args.from_channel))
        pprint(list(from_files.keys()))
        sys.exit(0)

    # Find the packages on the source channel that match the packages specified
    # on the command line
    if args.all:
        matched = list(from_files.keys())
    else:
        matched = [f for f in from_files.keys()
                   for p in args.packages if p in f]
    # and print them out
    print("""
    Packages that match {} on {}/{}/{}
""".format(args.packages, args.from_domain, args.from_owner, args.from_channel))
    pprint(matched)

    # get the package metadata on the target channel
    to_packages = to_cli.show_channel(args.to_channel, args.to_owner)
    to_files = {f['basename']: f for f in to_packages['files']}
    # figure out which of these packages actually need to be copied
    to_copy = [f for f in matched if f not in to_files.keys()]

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
    download_dir = tempfile.TemporaryDirectory(prefix='mirror')

    upload_cmd = ['anaconda',
                  '--site', args.to_domain,
                  '-t', args.to_token,
                  'upload', 
                  '-u', args.to_owner,]
    for copy_filename in to_copy:
        # get the full metadata
        md = from_files[copy_filename]
        login, package_name, version, platform, filename = md['full_name'].split('/')
        destination = os.path.join(download_dir.name, filename)
        print("Downloading {} to {}".format(md['basename'], destination))
        ret = from_cli.download(login, package_name, md['version'], md['basename'])
        with open(destination, 'wb') as f:
            f.write(ret.content)
        assert os.stat(destination).st_size == md['size']
    
        stdout, stderr, returncode = Popen(upload_cmd + [destination], cwd=download_dir.name)
        if returncode != 0:
            print("""
    stderr from {}
""".format(upload_cmd))
            pprint(stderr)
            sys.exit(1)
    sys.exit(0) 
    upload_cmd = ['anaconda',
                  '--site', args.to_domain,
                  'upload', 
                  '-u', args.to_owner,
                  '-t', args.to_token,
                  '*'] 

    stdout, stderr, returncode = Popen(upload_cmd, cwd=download_dir.name)
    if returncode != 0:
        print("""
    stderr from {}
""".format(upload_cmd))
        pprint(stderr)
        sys.exit(1)
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
            sys.exit(1)


if __name__ == "__main__":
    cli()
