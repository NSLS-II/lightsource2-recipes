import pdb
import sys
import traceback
import subprocess
import os
import time
import logging
import yaml
from conda_build.metadata import MetaData
import signal
from pprint import pformat, pprint
# create the anaconda cli
import binstar_client
from argparse import Namespace


current_subprocs = set()
shutdown = False


def handle_signal(signum, frame):
    # send signal recieved to subprocesses
    global shutdown
    shutdown = True
    for proc in current_subprocs:
        if proc.poll() is None:
            proc.send_signal(signum)
    print("Killing build script due to receiving signum={}"
          "".format(signum))
    sys.exit(1)


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def get_file_names_on_anaconda_channel(username, anaconda_cli,
                                       channel='main'):
    """Get the names of **all** the files on anaconda.org/username

    Parameters
    ----------
    username : str
    anaconda_cli : return value from binstar_client.utils.get_binstar()
    channel : str, optional
        The channel on anaconda.org/username to upload to.
        Defaults to 'main'

    Returns
    -------
    set
        The file names of all files on an anaconda channel.
        Something like 'linux-64/album-0.0.2.post0-0_g6b05c00_py27.tar.bz2'
    """
    return set([f['basename']
                for f in anaconda_cli.show_channel(channel, username)['files']])


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
        current_subprocs.add(proc)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        # pdb.set_trace()
    stdout, stderr = proc.communicate()
    current_subprocs.remove(proc)
    return stdout.decode(), stderr.decode(), proc.returncode


def check_output(cmd):
    try:
        ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        print(cmd)
        print(cpe.output.decode())
        raise RuntimeError("{} raised with check_output comand {}".format(
            cpe.output.decode(), cmd))
    else:
        name = ret.decode().strip().split('\n')
        return name


def determine_build_name(path_to_recipe, *conda_build_args):
    """Figure out what conda says the output built package name is going to be
    Parameters
    ----------
    path_to_recipe : str
        The location of the recipe on disk
    *conda_build_args : list
        List of extra arguments to be appeneded to the conda build command.
        For example, this might include ['--python', '3.4'], to tell
        conda-build to build a python 3.4 package

    Returns
    -------
    package_name : str
        Something like:
        /home/edill/mc/conda-bld/linux-64/pims-0.3.3.post0-0_g1bea480_py27.tar.bz2
    """
    conda_build_args = [] if conda_build_args is None else list(conda_build_args)
    cmd = ['conda', 'build', path_to_recipe, '--output'] + conda_build_args
    ret = check_output(cmd)
    if len(ret) > 1:
        # Then this is the first time we are getting the build name and conda
        # has to check out the source. Call it a second time and you get the4
        # full path to the file that will be spit out by conda-build
        return determine_build_name(path_to_recipe, *conda_build_args)
    # we want to keep track of the exact command so we can run it later.
    # Obviously drop the `--output` flag so that conda-build actually builds
    # the package.
    cmd.remove('--output')
    return ret[0], cmd


def run_build(recipes_path, anaconda_cli, username, pyver,
              token=None, npver=None):
    """Build and upload packages that do not already exist at {{ username }}

    Parameters
    ----------
    recipes_path : str
        Folder where the recipes are located
    anaconda_cli : return value from binstar_client.utils.get_binstar()
    username : str
        The anaconda user to upload all the built packages to
    pyver : list
        The python versions that need to be build. Should be a list of python
        versions to be passed to conda-build /path --python pyver.
        ['2.7', '3.4', '3.5']
    token : str, optional
        The binstar token that should be used to upload packages to
        anaconda.org/username. If no token is provided, no uploading will occur
    npver : str, optional
    """
    if npver is None:
        npver = os.environ.get("CONDA_NPY", "1.11")
    if token is None:
        print("No binstar token available. There will be no uploading."
              "Consider setting the BINSTAR_TOKEN environmental "
              "variable or passing one in via the --token command "
              "line argument")
    # get all file names that are in the channel I am interested in
    packages = get_file_names_on_anaconda_channel(username, anaconda_cli)

    dont_build = []
    to_build = []
    print("Determining package build names...")
    print('{: <8} | {}'.format('to build', 'built package name'))
    logging.info("Build Plan")
    for folder in sorted(os.listdir(recipes_path)):
        recipe_dir = os.path.join(recipes_path, folder)
        for py in pyver:
            try:
                path_to_built_package, build_cmd = determine_build_name(
                    recipe_dir, '--python', py, '--numpy', '1.10')
            except RuntimeError as re:
                logging.error(re)
                continue
            name_on_anaconda = os.sep.join(
                path_to_built_package.split(os.sep)[-2:])
            # pdb.set_trace()
            meta = MetaData(recipe_dir)
            on_anaconda_channel = name_on_anaconda in packages
            if on_anaconda_channel:
                dont_build.append((path_to_built_package, name_on_anaconda,
                                   build_cmd, meta))
            else:
                to_build.append((path_to_built_package, name_on_anaconda,
                                 build_cmd, meta))

            logging.info('{:<8} | {}'.format(
                         str(not bool(on_anaconda_channel)), name_on_anaconda))
    # build all the packages that need to be built
    UPLOAD_CMD = ['anaconda', '-t', token, 'upload', '-u',
                  username]
    # pdb.set_trace()
    no_token = []
    uploaded = []
    upload_failed = []
    build_or_test_failed = []
    # for each package
    for full_path, pkg_name, cmd, metadata in to_build:
        # output the package build name
        print("Building: %s"% pkg_name)
        # output the build command
        print("Build cmd: %s" % ' '.join(cmd))
        stdout, stderr, returncode = Popen(cmd)
        if returncode != 0:
            build_or_test_failed.append(pkg_name)
            pprint('stdout\n', stdout)
            pprint('stderr\n', stderr)
            continue
        if token:
            print("UPLOAD START")
            stdout, stderr, returncode = Popen(UPLOAD_CMD + [full_path])
            if returncode != 0:
                pprint('stdout\n', stdout)
                pprint('stderr\n', stderr)
                upload_failed.append(pkg_name)
                continue
            uploaded.append(pkg_name)
            continue

        no_token.append(pkg_name)

    return {
        'alreadybuilt': sorted([dont[1] for dont in dont_build]),
        'uploaded': sorted(uploaded),
        'no_token': sorted(no_token),
        'upload_failed': sorted(upload_failed),
        'build_or_test_failed': sorted(build_or_test_failed),
    }


def set_binstar_upload(on=False):
    """Turn on or off binstar uploading

    Parameters
    ----------
    on : bool, optional
        True: turn on binstar uploading
        False: turn off binstar uploading
        Defaults to False

    Raises exception if disabling binstar upload fails
    """
    rcpath = os.path.join(os.path.expanduser('~'), '.condarc')
    with open(rcpath, 'r') as f:
        rc = yaml.load(f.read())
    binstar_upload = rc.get('binstar_upload', False)
    if binstar_upload != on:
        rc['binstar_upload'] = on
        with open(rcpath, 'w') as f:
            # write the new yaml in `rcpath`
            f.write(yaml.dump(rc))


def cli():
    from argparse import ArgumentParser
    p = ArgumentParser(
        description="""
Tool for building a folder of conda recipes where only the ones that don't
already exist are built.
""",
    )
    p.add_argument(
        'recipes_path',
        nargs='?',
        help="path to recipes that should be built"
    )
    p.add_argument(
        '-p', "--pyver",
        action='store',
        nargs='*',
        help="Directory to write recipes to (default: %(default)s).",
        default=["2.7", "3.4", "3.5"],
    )
    p.add_argument(
        '-t', '--token', action='store',
        nargs='?',
        help='Binstar token to use to upload build packages',
        default=None
    )
    p.add_argument(
        '-l', '--log',
        nargs='?',
        help='Name of the log file to write'
    )
    p.add_argument(
        "-s", "--site",
        nargs='?',
        help='Anaconda upload api (defaults to %(default)s',
        default='https://api.anaconda.org'
    )
    p.add_argument(
        "-u", "--username",
        action="store",
        nargs='?',
        help=("Username to upload package to")
    )
    p.add_argument(
        '--npver', action='store', nargs='*',
        help=('List the numpy versions to build packages for. Defaults to '
              '%(default)s'),
        default=['1.11']
    )
    args = p.parse_args()
    if args.token is None and 'BINSTAR_TOKEN' in os.environ:
        args.token = os.environ.get('BINSTAR_TOKEN')
    # pdb.set_trace()
    args.recipes_path = os.path.abspath(args.recipes_path)
    print(args)
    # pdb.set_trace()
    run(**dict(args._get_kwargs()))

def run(recipes_path, pyver, log, site, username, token, npver):
    # set up logging
    if not log:
        log_dirname = os.path.join(os.path.expanduser('~'),
                                      'auto-build-logs', 'dev')
        os.makedirs(log_dirname, exist_ok=True)
        log_filename = time.strftime("%m.%d-%H.%M")
        log = os.path.join(log_dirname, log_filename)
    FORMAT = "%(levelname)s | %(asctime)-15s | %(message)s"
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log)
    logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                        handlers=[stream_handler, file_handler])
    # build all python versions by default
    if not pyver:
        pyver = ['2.7', '3.4', '3.5']
    # check to make sure that the recipes_path exists
    if not os.path.exists(recipes_path):
        logging.Error("The recipes_path: '%s' does not exist." % recipes_path)
        sys.exit(1)
    print('token={}'.format(token))
    # just disable binstar uploading whenever this script is running.
    print('Disabling binstar upload. If you want to turn it back on, '
          'execute: `conda config --set binstar_upload true`')
    set_binstar_upload(False)
    # set up logging
    full_recipes_path = os.path.abspath(recipes_path)
    print('Logging summary to %s' % log)

    # site = 'https://pergamon.cs.nsls2.local:8443/api'
    # os.environ['REQUESTS_CA_BUNDLE'] = '/etc/certificates/ca_cs_nsls2_local.crt'

    anaconda_cli = binstar_client.utils.get_binstar(Namespace(token=token,
                                                              site=site))
    try:
        results = run_build(full_recipes_path, anaconda_cli, username,
                            pyver, token=token, npver=npver)
    except Exception as e:
        logging.error("Major error encountered in attempt to build {}"
                      "".format(full_recipes_path))
        logging.error("Error in run_build!")
        logging.error(e)
        logging.error("Full stack trace")
        logging.error(traceback.format_exc())
    else:
        logging.info("Build summary")
        logging.info('Expected {} packages'.format(
            len(pyver) * len(os.listdir(full_recipes_path))))
        num_builds = {k: len(v) for k, v in results.items()}
        logging.info('Got {} packages.'.format(
            sum([n for n in num_builds.values()])))
        logging.info('Breakdown is as follows')
        for k, v in num_builds.items():
            logging.info('section: {:<25}. number build: {}'.format(k, v))
        if results['build_or_test_failed']:
            logging.error("Some packages failed to build")
            logging.error(pformat(results['build_or_test_failed']))
        if results['no_token']:
            logging.error("No anaconda token. Cannot upload these packages")
            logging.error(pformat(results['no_token']))
        if results['upload_failed']:
            logging.error('Upload failed for these packages')
            logging.error(pformat(results['upload_failed']))
        if results['alreadybuilt']:
            logging.info('Packages that already exist in {}'.format(username))
            logging.info(pformat(results['alreadybuilt']))
        if results['uploaded']:
            logging.info('Packages that were built and uploaded')
            logging.info(pformat(results['uploaded']))
    finally:
        # close the file handler
        file_handler.close()



if __name__ == "__main__":
    run('../staged-recipes-dev/pyall/xray-vision', ['2.7'], None, None,
        'ericdill', None)
