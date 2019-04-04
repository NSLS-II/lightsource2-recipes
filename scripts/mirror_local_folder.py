#!/usr/bin/env python
"""
CLI to mirror all files in a package from one conda channel to another

"""
import os
from argparse import ArgumentParser
from pprint import pformat
import sys
import subprocess
import tempfile
import logging
import traceback
import glob

import binstar_client
import slacker

logger = logging.getLogger('mirror_local_folder.py')


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
        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                *args, **kwargs)
    except subprocess.CalledProcessError as cpe:
        logger.error(cpe)
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
    p.add_argument(
        '--log',
        nargs="?",
        action="store",
        help="File to log to",
    )
    p.add_argument(
        '--slack-token',
        action='store',
        nargs='?',
        help=("Slack authentication token"),
    )
    p.add_argument(
        '--slack-channel',
        action='store',
        nargs='?',
        help=("Slack channel to post to"),
        default="bob-the-builder",
    )
    args = p.parse_args()
    args.to_channel = 'main'
    args.from_channel = 'main'

    # init some logging
    if args.log:
        stream = logging.StreamHandler()
        filehandler = logging.FileHandler(args.log, mode='a')
        stream.setLevel(logging.INFO)
        filehandler.setLevel(logging.INFO)
        logger.addHandler(stream)
        logger.addHandler(filehandler)
        logger.setLevel(logging.INFO)
        logger.info("Logging to {}".format(args.log))

    # set up slack integration
    slack_token = args.slack_token
    slack_channel = args.slack_channel
    slack_api = slacker.Slacker(slack_token)
    try:
        ret = slack_api.auth.test()
    except slacker.Error as e:
        slack_api = None
        if slack_token is None:
            logger.info('No slack token provided. Not sending messages to '
                        'slack')
        else:
            logger.error('slack_token {} does grant access to the {} channel'
                         ''.format(slack_token, slack_channel))
            logger.error(traceback.format_exc())
            logger.error(e)
    else:
        logger.info("Slack authentication successful.")
        logger.info("Authenticating as the %s user", ret.body['user'])
        logger.info("Authenticating to the %s team", ret.body['team'])

    logger.info("\nSummary")
    logger.info("-------")
    logger.info("Mirroring from {} at {}".format(args.from_owner,
                                                 args.from_domain))
    logger.info("Mirroring to {} at {}".format(args.to_owner, args.to_domain))
    logger.info("\nPlatforms")
    logger.info("---------")
    logger.info(pformat(args.platform))
    logger.info("\nPackages list")
    logger.info("-------------")
    if args.all:
        logger.info("**all packages**")
    else:
        logger.info(pformat(args.packages))
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

    # Get the package metadata from the specified anaconda channel
    from_packages = from_cli.show_channel(args.from_channel,
                                          args.from_owner)
    if ',' in args.platform[0]:
        pt_list = args.platform[0].split(',')
    else:
        pt_list = args.platform
    # only focus on one platform
    pt = pt_list[0]
    from_files = {f['basename']: f for f in from_packages['files']
                  if pt in f['full_name']}
    # f['attrs'] may not have key 'subdir'
    #from_files = {f['basename']: f for f in from_packages['files']
    #              if f['attrs']['subdir'] in pt}
    
    if args.list:
        # print out the list of all files on the source channel and exit
        logger.info("\nComplete files list on {} at {}:".format(
            args.from_owner, args.from_domain))
        logger.info("-------------------")
        logger.info(pformat(sorted(list(from_files.keys()))))
        sys.exit(0)

    # Find the packages on the source channel that match the packages specified
    # on the command line
    if args.all:
        matched = list(from_files.keys())
    else:
        matched = [f for f in from_files.keys()
                   for p in args.packages if p in f]
    # and print them out
    logger.info("\nFiles that exist on {} at {}:".format(args.from_owner,
                                                         args.from_domain))
    logger.info(pformat(sorted(matched)))

    # get the package metadata on the target channel
    #to_packages = to_cli.show_channel(args.to_channel, args.to_owner)
    
    # folder is at /www/conda/channel_name/
    download_dir = os.path.join(os.sep, 'www', 'conda', 
                                args.to_owner, pt)
    files_existed = glob.glob(os.path.join(download_dir, '*'))
    to_files = [f.split(os.sep)[-1] for f in files_existed]
    
    # figure out which packages already exist
    already_exist = [f for f in matched if f.split(os.sep)[-1] in to_files]
    logger.info("\nFiles that already exist on {} at {}:".format(
        args.to_owner, args.to_domain))
    logger.info(pformat(sorted(already_exist)))
    # figure out which of these packages actually need to be copied
    to_copy = [f for f in matched if f.split(os.sep)[-1] not in to_files]
    # print out the packages that need to be copied
    logger.info(pformat(sorted(to_copy)))

    logger.info('number of files to copy: {}'.format(len(to_copy)))
    
    if args.dry_run:
        # don't upload anything.  Print out why we are quitting and then quit
        logger.info("\nExiting because --dry-run flag is set")
        sys.exit(0)
    
    for copy_filename in to_copy:
        # get the full metadata
        md = from_files[copy_filename]
        (login, package_name,
            version, platform, filename) = md['full_name'].split('/')
        destination = os.path.join(download_dir, filename)
        logger.info("Downloading {} to {}".format(md['basename'],
                                                  destination))
        ret = from_cli.download(
            login, package_name, md['version'], md['basename'])
        
        with open(destination, 'wb+') as f:
            f.write(ret.content)
        assert os.stat(destination).st_size == md['size']
        message = '{} to {} at {}\n'.format(filename,
                                            args.to_owner,
                                            destination)
        logger.info('Uploading {}'.format(message))
        #stdout, stderr, returncode = Popen(upload_cmd + [destination])
        if slack_api:
            slack_api.chat.post_message(
                slack_channel, "Mirrored {}".format(message))

    logger.info("Script complete.")

if __name__ == "__main__":
    cli()
