import pdb
import sys
import traceback
import subprocess
import os
import time
import logging
import yaml
from conda_build.metadata import MetaData
import click
import signal

current_subprocs = set()
shutdown = False

def handle_signal(signum, frame):
    # send signal recieved to subprocesses
    global shutdown
    shutdown = True
    for proc in current_subprocs:
        if proc.poll() is None:
            proc.send_signal(signum)
    logging.error("Killing build script due to receiving signum={}"
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
                for f in anaconda_cli.show_channel('main', username)['files']])


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
        pdb.set_trace()
    stdout, stderr = proc.communicate()
    current_subprocs.remove(proc)
    return proc.returncode


def check_output(cmd):
    try:
        ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        logging.error(cmd)
        logging.error(cpe.output.decode())
        raise RuntimeError("{} raised with check_output comand {}".format(
            cpe.output.decode(), cmd))
    else:
        return ret.decode().strip().split('\n')


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


def run_build(recipes_path, log_filename, anaconda_cli, username, pyver,
              token=None):
    """Build and upload packages that do not already exist at {{ username }}

    Parameters
    ----------
    recipes_path : str
        Folder where the recipes are located
    log_filename : str
        Filename to log to
    anaconda_cli : return value from binstar_client.utils.get_binstar()
    username : str
        The anaconda user to upload all the built packages to
    pyver : list
        The python versions that need to be build. Should be a list of python
        versions to be passed to conda-build /path --python pyver.
        ['2.7', '3.4', '3.5']
    token : str
        The binstar token that should be used to upload packages to
        anaconda.org/username
    """
    FORMAT = "%(levelname)s | %(asctime)-15s | %(message)s"
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log_filename)
    logging.basicConfig(level=logging.DEBUG, format=FORMAT,
                        handlers=[stream_handler, file_handler])

    if token is None:
        logging.error("No binstar token available. There will be no uploading."
                      "Consider setting the BINSTAR_TOKEN environmental "
                      "variable or passing one in via the --token command "
                      "line argument")
    # get all file names that are in the channel I am interested in
    lightsource2_packages = get_file_names_on_anaconda_channel(
        'lightsource2-dev', anaconda_cli)

    dont_build = []
    to_build = []
    logging.info("Determining package build names...")
    logging.info('{: <8} | {}'.format('to build', 'built package name'))
    for folder in sorted(os.listdir(recipes_path)):
        recipe_dir = os.path.join(recipes_path, folder)
        for py in pyver:
            try:
                path_to_built_package, build_cmd = determine_build_name(
                    recipe_dir, '--python', py)
            except RuntimeError:
                continue
            name_on_anaconda = os.sep.join(
                path_to_built_package.split(os.sep)[-2:])
            meta = MetaData(recipe_dir)
            on_anaconda_channel = name_on_anaconda in lightsource2_packages
            if on_anaconda_channel:
                dont_build.append((path_to_built_package, name_on_anaconda,
                                   build_cmd, meta))
            else:
                to_build.append((path_to_built_package, name_on_anaconda,
                                    build_cmd, meta))

            logging.info('{:<8} | {}'.format(str(not bool(on_anaconda_channel)), name_on_anaconda))
    # build all the packages that need to be built
    UPLOAD_CMD = ['anaconda', '-t', token, 'upload', '-u',
                  username]
    # for each package
    for full_path, pkg_name, cmd, metadata in to_build:
        # output the package build name
        logging.info("Building: %s"% pkg_name)
        # output the build command
        logging.info("Build cmd: %s" % ' '.join(cmd))
        returncode = Popen(cmd)
        logging.info("Return code {}".format(returncode))
        if token:
            logging.info("UPLOAD START")
            returncode = Popen(UPLOAD_CMD + [full_path])
            logging.info("Return code {}".format(returncode))


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


@click.command()
@click.argument('recipes_path', nargs=1)
@click.argument('pyver', nargs=-1)
@click.option('--token', envvar='BINSTAR_TOKEN',
              help='Binstar token to use to upload built packages')
@click.option('--log', help='Name of the log file to write')
@click.option('--site', help='Anaconda upload api (defaults to https://api.anaconda.org')
@click.option('--username', help='Username to upload package to')
def cli(recipes_path, pyver, token, log, username, site=None):
    if not pyver:
        pyver = ['2.7', '3.4', '3.5']
    if not os.path.exists(recipes_path):
        print("Error!")
        print("The path '%s' does not exist." % recipes_path)
        sys.exit(1)

    # just disable binstar uploading whenever this script is running.
    print('Disabling binstar upload. If you want to turn it back on, '
          'execute: `conda config --set binstar_upload true`')
    set_binstar_upload(False)

    # set up logging
    full_recipes_path = os.path.abspath(recipes_path)
    if not log:
        log_dirname = os.path.join(os.path.expanduser('~'),
                                      'auto-build-logs', 'dev')
        os.makedirs(log_dirname, exist_ok=True)
        log_filename = time.strftime("%m.%d-%H.%M")
        log = os.path.join(log_dirname, log_filename)
    print('Logging output to %s' % log)

    # create the anaconda cli
    import binstar_client
    from binstar_client import Binstar
    from argparse import Namespace
    at_nsls2 = True
    try:
        ret = subprocess.call(['ping', 'pergamon', '-c', '5'], timeout=1).decode().strip()
        if 'unknown host' in ret:
            at_nsls2 = False
    except subprocess.TimeoutExpired:
        # we are probably not at nsls2
        at_nsls2 = False

    # site = 'https://pergamon.cs.nsls2.local:8443/api'
    # os.environ['REQUESTS_CA_BUNDLE'] = '/etc/certificates/ca_cs_nsls2_local.crt'

    anaconda_cli = binstar_client.utils.get_binstar(Namespace(token=token,
                                                              site=site))
    try:
        run_build(full_recipes_path, log, anaconda_cli, username, pyver)
    except Exception as e:
        print("Error in run_build!")
        print(e)
        print("Full stack trace")
        print(traceback.format_exc())

    if at_nsls2:
        del os.environ['REQUESTS_CA_BUNDLE']


if __name__ == "__main__":
    cli('/home/edill/dev/conda/staged-recipes-dev/py2', ['2.7'])
