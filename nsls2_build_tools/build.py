from argparse import ArgumentParser
import pdb
import yaml
import sys
import traceback
import subprocess
import os
import time
import logging
import yaml
import networkx as nx
import copy
from conda_build.metadata import MetaData
import signal
from pprint import pformat, pprint
# create the anaconda cli
import binstar_client
from argparse import Namespace
import itertools
import tempfile
import getpass

current_subprocs = set()
shutdown = False

DEFAULT_PY = '3.5'
DEFAULT_NP_VER = '1.11'


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


def get_anaconda_cli(token=None, site=None):
    if token is None:
        token = get_binstar_token()
    return binstar_client.utils.get_server_api(token=token, site=site)


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
    """Returns stdout, stderr and the return code

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
    if stdout:
        stdout = stdout.decode()
    if stderr:
        stderr = stderr.decode()
    current_subprocs.remove(proc)
    return stdout, stderr, proc.returncode


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
    conda_build_args = [] if conda_build_args is None else list(
        conda_build_args)
    logging.debug('conda_build_args=%s', conda_build_args)
    cmd = ['conda', 'build', path_to_recipe, '--output'] + conda_build_args
    logging.debug('cmd=%s', cmd)
    ret = check_output(cmd)
    logging.debug('ret=%s', ret)
    # if len(ret) > 1:
    #     logging.debug('recursing...')
    #     # Then this is the first time we are getting the build name and conda
    #     # has to check out the source. Call it a second time and you get the4
    #     # full path to the file that will be spit out by conda-build
    #     return determine_build_name(path_to_recipe, *conda_build_args)
    # we want to keep track of the exact command so we can run it later.
    # Obviously drop the `--output` flag so that conda-build actually builds
    # the package.
    cmd.remove('--output')
    logging.debug('cmd=%s', cmd)
    return ret[-1], cmd


def decide_what_to_build(recipes_path, python, packages, numpy):
    """Figure out which packages need to be built

    Parameters
    ----------
    recipes_path : str
        Path to folder containg conda recipes
    python : list
        List of python versions to build
    packages : list
        List of packages that already exist on the anaconda channel we are
        interested in
    numpy : list
        List of numpy versions to build.

    Returns
    -------
    metas_to_build : list
        the metadata for the conda build with three extra fields:
            - full_build_path
            - build_name
            - build_command
    metas_not_to_build : list
        Same as `packages_to_build`
    """

    metas_not_to_build = []
    metas_to_build = []
    # logging.info("Build Plan")
    # logging.info("Determining package build names...")
    # logging.info('{: <8} | {}'.format('to build', 'built package name'))
    recipes_path = os.path.abspath(recipes_path)
    logging.info("recipes_path = {}".format(recipes_path))
    for folder in sorted(os.listdir(recipes_path)):
        recipe_dir = os.path.join(recipes_path, folder)
        if os.path.isfile(recipe_dir):
            continue
        if 'meta.yaml' not in os.listdir(recipe_dir):
            continue
        logging.debug('Evaluating recipe: {}'.format(recipe_dir))
        build, run, test = get_deps_from_metadata(recipe_dir)
        # only need to do multiple numpy builds if the meta.yaml pins the numpy
        # version in build and run.
        numpy_build_versions = numpy
        if 'numpy x.x' not in build:
            numpy_build_versions = [DEFAULT_NP_VER]
        python_build_versions = python
        if 'python' not in set(build + run):
            python_build_versions = [DEFAULT_PY]
        for py, npy in itertools.product(python_build_versions,
                                         numpy_build_versions):
            logging.debug("Checking py={} and npy={}".format(py, npy))
            try:
                os.environ['CONDA_NPY'] = npy
                path_to_built_package, build_cmd = determine_build_name(
                    recipe_dir, '--python', py, '--numpy', npy)
                del os.environ['CONDA_NPY']
            except RuntimeError as re:
                logging.error(re)
                continue
            if '.tar.bz' not in path_to_built_package:
                on_anaconda_channel = True
                name_on_anaconda = "Skipping {}".format(
                    folder, py, npy
                )
            else:
                name_on_anaconda = os.sep.join(
                    path_to_built_package.split(os.sep)[-2:])
                # pdb.set_trace()
                meta = MetaData(recipe_dir)
                on_anaconda_channel = name_on_anaconda in packages
                meta.full_build_path = path_to_built_package
                meta.build_name = name_on_anaconda
                meta.build_command = build_cmd
                if on_anaconda_channel:
                    metas_not_to_build.append(meta)
                else:
                    metas_to_build.append(meta)

            logging.info('{:<8} | {:<5} | {:<5} | {}'.format(
                str(not bool(on_anaconda_channel)), py, npy, name_on_anaconda))

    return metas_to_build, metas_not_to_build


def get_deps_from_metadata(path):
    """
    Extract all dependencies from a recipe. Return tuple of (build, run, test)
    """
    meta = MetaData(path)
    test = meta.meta.get('test', {}).get('requires', [])
    run = meta.meta.get('requirements', {}).get('run', [])
    build = meta.meta.get('requirements', {}).get('build', [])
    return build or [], run or [], test or []

def sanitize_names(list_of_names):
    list_of_names = [name.split(' ')[0] for name in list_of_names]
    list_of_names = [name for name in
                     list_of_names]  # if name not in packages_on_conda_forge]
    return list_of_names


def build_dependency_graph(metas):
    """
    Given an input list of MetaData objects, build a directional graph of
    how the dependencies are related.  Gotchas include determining the
    package name without the version pinning and without conda selectors.

    Parameters
    ----------
    metas : iterable of MetaData objects

    Returns
    -------
    graph
        Networkx graph object

    Notes
    -----
    Example of version pinning:
    requirements:
        build:
            numpy >=1.11

    Example of selectors:
    requirements:
        build:
            python  # [not py2k]
    """
    run_deps = {}
    build_deps = {}
    logging.debug("Building dependency graph for %s libraries", len(metas))

    for meta in metas:
        name = meta.meta['package']['name']
        logging.debug('name=%s', name)
        build_deps[name] = sanitize_names(
            meta.meta.get('requirements', {}).get('build', []))
        logging.debug('build_deps=%s', build_deps)
        run_deps[name] = sanitize_names(
            meta.meta.get('requirements', {}).get('run', []))
        logging.debug('run_deps=%s', run_deps)
    # pdb.set_trace()
    union = copy.deepcopy(build_deps)
    for package, deps in run_deps.items():
        union[package] = set(build_deps.get(package) + run_deps.get(package))
    # logging.debug()
    # drop all extra packages that I do not have conda recipes for
    for name, items in union.items():
        union[name] = [item for item in items if item in union]

    return resolve_dependencies(union)


def resolve_dependencies(package_dependencies):
    """
    Given a dictionary mapping a package to its dependencies, return a
    generator of packages to install, sorted by the required install
    order.

    >>> deps = resolve_dependencies({'a': ['b', 'c'], 'b': ['c'],
                                     'c': ['d'], 'd': []})
    >>> list(deps)
    ['d', 'c', 'b', 'a']

    """
    remaining_dependencies = package_dependencies.copy()
    completed_packages = []

    # A maximum of 10000 iterations. Beyond that and there is probably a
    # problem.
    for failsafe in range(10000):
        for package, deps in sorted(remaining_dependencies.copy().items()):
            if all(dependency in completed_packages for dependency in deps):
                completed_packages.append(package)
                remaining_dependencies.pop(package)
                yield package
            else:
                # Put a check in to ensure that all the dependencies were
                # defined as packages, otherwise we will never succeed.
                for dependency in deps:
                    if dependency not in package_dependencies:
                        msg = ('The package {} depends on {}, but it was not '
                               'part of the package_dependencies dictionary.'
                               ''.format(package, dependency))
                        raise ValueError(msg)

        # Close off the loop if we've completed the dependencies.
        if not remaining_dependencies:
            break
    else:
        raise ValueError('Dependencies could not be resolved. '
                         'Remaining dependencies: {}'
                         ''.format(remaining_dependencies))


def run_build(metas, username, token=None, upload=True):
    """Build and upload packages that do not already exist at {{ username }}

    Parameters
    ----------
    metas : iterable
    recipes_path : str
        Iterable of conda build Metadata objects.
        HINT: output of `decide_what_to_build` is probably what should be
        passed in here
    username : str
        The anaconda user to upload all the built packages to
    token : str, optional
        The binstar token that should be used to upload packages to
        anaconda.org/username. If no token is provided, no uploading will occur
    upload : bool, optional
        Whether or not to upload packages. If True, requires `token` to be set.
        The reason why there is this additional flag is that sometimes you need
        a token to authenticate to a channel to see if packages already exist
        but you might not want to upload that package.
    """
    if token is None:
        token = get_binstar_token()
    metas_name_order = build_dependency_graph(metas)
    # pdb.set_trace()
    print('dependency_graph=%s' % metas_name_order)
    # metas_name_order = resolve_dependencies(dependency_graph)
    build_order = [meta for name in metas_name_order for meta in metas
                   if meta.meta['package']['name'] == name]
    # print('metas_order = {}'.format(metas_order))
    # build_order = builder.sort_dependency_order(metas)
    logging.info("Build Order.")
    for meta in build_order:
        logging.info(meta.build_name)

    no_token = []
    uploaded = []
    upload_failed = []
    build_or_test_failed = []
    UPLOAD_CMD = ['anaconda', '-t', token, 'upload', '-u', username]
    # for each package
    for meta in build_order:
        full_build_path = meta.full_build_path
        build_name = meta.build_name
        build_command = meta.build_command
        # output the package build name
        print("Building: %s" % build_name)
        # # need to run the build command with --output again or conda freaks out
        # stdout, stderr, returncode = Popen(build_command + ['--output'])
        # output the build command
        print("Build cmd: %s" % ' '.join(build_command))
        np = None
        try:
            np_idx = build_command.index('--numpy')
        except ValueError:
            # --numpy is not in build_command
            pass
        else:
            np = build_command[np_idx+1]
        if np:
            os.environ['CONDA_NPY'] = np
        stdout, stderr, returncode = Popen(build_command)
        if np:
            del os.environ['CONDA_NPY']
        if returncode != 0:
            build_or_test_failed.append(build_name)
            logging.error('\n\n========== STDOUT ==========\n')
            logging.error(pformat(stdout))
            logging.error('\n\n========== STDERR ==========\n')
            logging.error(pformat(stderr))
            continue
        if token and upload:
            print("UPLOAD START")
            cmd = UPLOAD_CMD + [full_build_path]
            cleaned_cmd = cmd.copy()
            cleaned_cmd[2] = 'SCRUBBED'
            print("Upload command={}".format(cleaned_cmd))
            stdout, stderr, returncode = Popen(cmd)
            if returncode != 0:
                logging.error('\n\n========== STDOUT ==========\n')
                logging.error(pformat(stdout))
                logging.error('\n\n========== STDERR ==========\n')
                logging.error(pformat(stderr))
                upload_failed.append(build_name)
                continue
            uploaded.append(build_name)
            continue

        no_token.append(build_name)

    return {
        'uploaded': sorted(uploaded),
        'no_token': sorted(no_token),
        'upload_failed': sorted(upload_failed),
        'build_or_test_failed': sorted(build_or_test_failed),
    }


def clone(git_url, git_rev=None):
    """Clone a `git_url` to temp dir and check out `git_rev`

    Parameters
    ----------
    git_url : str
        Git repo to clone
    git_rev : str, optional
        Branch to check out
        Defaults to whatever the repo thinks is the master branch

    Returns
    -------
    path : str
        Full path to root of newly cloned git repo
    """
    if git_rev is None:
        git_rev = 'master'
    logging.info("Cloning url={}. rev={}".format(git_url, git_rev))
    tempdir = tempfile.gettempdir()
    sourcedir = os.path.join(tempdir, getpass.getuser(), git_url.strip('/').split('/')[-1])
    if not os.path.exists(sourcedir):
        # clone the git repo to the target directory
        print('Cloning to %s', sourcedir)
        subprocess.call(['git', 'clone', git_url, sourcedir])
    return sourcedir


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


def get_binstar_token():
    token = os.environ.get('BINSTAR_TOKEN')
    if not token:
        print("No binstar token available. There will be no uploading."
              "Consider setting the BINSTAR_TOKEN environmental "
              "variable or passing one in via the --token command "
              "line argument")
    return token


def pdb_hook(exctype, value, traceback):
    pdb.post_mortem(traceback)


def cli():
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
        '-p', "--python",
        action='store',
        nargs='*',
        help="Python version to build conda packages for",
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
        '--numpy', action='store', nargs='*',
        help=('List the numpy versions to build packages for. Defaults to '
              '%(default)s'),
        default=[DEFAULT_NP_VER]
    )
    p.add_argument(
        '--no-upload', action='store_true', default=False,
        help="This flag disables uploading"
    )
    p.add_argument(
        '-v', '--verbose', help="Enable DEBUG level logging. Default is INFO",
        default=False, action="store_true"
    )
    p.add_argument(
        '--pdb', help="Enable PDB debugging on exception",
        default=False, action="store_true"
    )
    args = p.parse_args()
    if not args.python:
        args.python = [DEFAULT_PY]
    args_dct = dict(args._get_kwargs())
    use_pdb = args_dct.pop('pdb')
    if use_pdb:
        # set the pdb_hook as the except hook for all exceptions
        sys.excepthook = pdb_hook
    loglevel = logging.DEBUG if args_dct.pop('verbose') else logging.INFO
    log = args_dct.pop('log')
    init_logging(log_file=log, loglevel=loglevel)

    args_dct['recipes_path'] = os.path.abspath(args.recipes_path)
    print(args)
    run(**args_dct)


def init_logging(log_file=None, loglevel=logging.INFO):
    if not log_file:
        log_dirname = os.path.join(os.path.expanduser('~'),
                                   'auto-build-logs')
        os.makedirs(log_dirname, exist_ok=True)
        log_filename = time.strftime("%m.%d-%H.%M")
        log = os.path.join(log_dirname, log_filename)
    # set up logging
    print('Logging summary to %s' % log)
    FORMAT = "%(levelname)s | %(asctime)-15s | %(message)s"
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log)
    logging.basicConfig(level=loglevel, format=FORMAT,
                        handlers=[stream_handler, file_handler])


def run(recipes_path, python, site, username, numpy, token=None,
        no_upload=False):
    # check to make sure that the recipes_path exists
    if not os.path.exists(recipes_path):
        logging.error("The recipes_path: '%s' does not exist." % recipes_path)
        sys.exit(1)
    # print('token={}'.format(token))
    # just disable binstar uploading whenever this script is running.
    print('Disabling binstar upload. If you want to turn it back on, '
          'execute: `conda config --set binstar_upload true`')
    set_binstar_upload(False)

    # site = 'https://pergamon.cs.nsls2.local:8443/api'
    # os.environ['REQUESTS_CA_BUNDLE'] = '/etc/certificates/ca_cs_nsls2_local.crt'

    anaconda_cli = get_anaconda_cli(token, site)
    if numpy is None:
        numpy = os.environ.get("CONDA_NPY", "1.11")
        if not isinstance(numpy, list):
            numpy = [numpy]
    # get all file names that are in the channel I am interested in
    packages = get_file_names_on_anaconda_channel(username, anaconda_cli)

    to_build, dont_build = decide_what_to_build(recipes_path, python, packages,
                                                numpy)
    safe_run_build(to_build, username, dont_build, token, not no_upload)


def safe_run_build(metas_to_build, username, metas_to_skip,
                   token=None, upload=True):
    try:
        if metas_to_build == []:
            raise Exception("No recipes to build! Exiting...")
        results = run_build(metas_to_build, username, token=token, upload=upload)
        results['alreadybuilt'] = sorted([skip.build_name
                                          for skip in metas_to_skip])
    except Exception as e:
        logging.error("Major error encountered in attempt to build")
        logging.error("Error in run_build!")
        logging.error(e)
        logging.error("Full stack trace")
        logging.error(traceback.format_exc())
        # exit with a failed status code
        sys.exit(1)
    else:
        logging.info("Build summary")
        logging.info('Expected {} packages'.format(len(metas_to_build)))
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


if __name__ == "__main__":
    init_logging(None, loglevel=logging.DEBUG)
    run('../staged-recipes-dev/pyall/xray-vision', ['2.7'], None,
        'ericdill', None)
