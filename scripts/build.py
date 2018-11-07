#!/usr/bin/env conda-execute
"""
CLI to build a folder full of recipes.

Example usage:

build.py /folder/of/recipes --python 2.7 3.4 3.5 --numpy 1.10 1.11 --token <your anaconda token>

build.py --help
"""

# conda execute
# env:
# - conda-build
# - anaconda-client
# - networkx
# - slacker
# run_with: python

import itertools
import logging
import os
import pdb
import signal
import subprocess
import sys
import time
import traceback
from argparse import ArgumentParser
from contextlib import contextmanager
from pprint import pformat
import slacker
import binstar_client
import yaml
from conda_build.metadata import MetaData

logger = logging.getLogger('build.py')
current_subprocs = set()
shutdown = False

DEFAULT_PY = '3.6'
DEFAULT_NP_VER = '1.14'
slack_channel = 'bob-the-builder'
slack_api = None
anaconda_cli = None


@contextmanager
def env_var(key, value):
    old_val = os.environ.get(key)
    os.environ[key] = value
    yield
    if old_val:
        os.environ[key] = old_val
    else:
        del os.environ[key]


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
    return binstar_client.Binstar(token=token, domain=site)


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
    return set(
        [f['basename']
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
        stdout = stdout.decode('utf-8')
    if stderr:
        stderr = stderr.decode('utf-8')
    current_subprocs.remove(proc)
    return stdout, stderr, proc.returncode


def check_output(cmd):
    try:
        ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as cpe:
        print(cmd)
        print(cpe.output.decode('utf-8'))
        raise RuntimeError("{} raised with check_output comand {}".format(
            cpe.output.decode('utf-8'), cmd))
    else:
        name = ret.decode('utf-8').strip().split('\n')
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
    logger.debug('conda_build_args=%s', conda_build_args)
    cmd = ['conda', 'build', path_to_recipe, '--output', '--old-build-string'] + conda_build_args
    logger.debug('cmd=%s', cmd)
    ret = check_output(cmd)
    logger.debug('ret=%s', ret)
    # if len(ret) > 1:
    #     logger.debug('recursing...')
    #     # Then this is the first time we are getting the build name and conda
    #     # has to check out the source. Call it a second time and you get the4
    #     # full path to the file that will be spit out by conda-build
    #     return determine_build_name(path_to_recipe, *conda_build_args)
    # we want to keep track of the exact command so we can run it later.
    # Obviously drop the `--output` flag so that conda-build actually builds
    # the package.
    cmd.remove('--output')
    logger.debug('cmd=%s', cmd)
    return ret[-1], cmd


def remove_hash_string(name):
    """Remove hash string to avoid duplicated package building.
    """
    hash_len = 8
    strlist = ['py27', 'py34', 'py35', 'py36']
    for v in strlist:
        py_pos = name.find(v)
        if py_pos != -1:
            break
    if py_pos == -1:
        logger.debug('hash string can not be removed')
        return name
    
    #standard format like "py36_1.tar.bz2", get loose bound, not 4+2+8
    len_limit = 4+2+4
    len_limit += hash_len # also consider hash_len
    if len(name) - py_pos > len_limit:
        name_new = name[:py_pos + 4] + name[py_pos + 4 + hash_len:]
    else:
        name_new = name
    return name_new


def get_simplified_name(name):
    "get package name without version number, only simplified name."
    return name.split(os.sep)[1].split('-')[0]


def group_packages(packages):
    "group packages based on simplified name."
    pkgs = list(packages)
    pkgs_dict = {}
    for v in pkgs:
        core_name = get_simplified_name(v) 
        if core_name not in pkgs_dict:
            pkgs_dict[core_name] = [v]
        else:
            pkgs_dict[core_name].append(v)
    return pkgs_dict


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

    # remove hash string for comparison
    packages_tmp = list(packages)
    packages_no_hash = [remove_hash_string(name) for name in packages_tmp]
    pkgs_dict = group_packages(packages_no_hash)

    # logger.info("Build Plan")
    # logger.info("Determining package build names...")
    # logger.info('{: <8} | {}'.format('to build', 'built package name'))
    recipes_path = os.path.abspath(recipes_path)
    logger.info("recipes_path = {}".format(recipes_path))
    for folder in sorted(os.listdir(recipes_path)):
        print(f'\n{"="*80}\n{os.path.basename(recipes_path)}\n{"="*80}\n')
        recipe_dir = os.path.join(recipes_path, folder)
        if os.path.isfile(recipe_dir):
            # Add support for single-package builds:
            if folder == 'meta.yaml':
                recipe_dir = recipes_path
            else:
                continue
        if 'meta.yaml' not in os.listdir(recipe_dir):
            continue
        logger.debug('Evaluating recipe: {}'.format(recipe_dir))
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
            logger.debug("Checking py={} and npy={}".format(py, npy))
            try:
                with env_var('CONDA_NPY', npy):
                    path_to_built_package, build_cmd = determine_build_name(
                        recipe_dir, '--python', py, '--numpy', npy)
            except RuntimeError as re:
                logger.error(re)
                continue
            if '.tar.bz' not in path_to_built_package:
                on_anaconda_channel = True
                name_on_anaconda = "Skipping {}".format(
                    folder, py, npy
                )
            else:
                name_on_anaconda = os.sep.join(
                    path_to_built_package.split(os.sep)[-2:])
                
                # choose which package to build without hash name
                name_no_hashstring = remove_hash_string(name_on_anaconda)
                
                # pdb.set_trace()
                #on_anaconda_channel = name_on_anaconda in packages
                #on_anaconda_channel = name_no_hashstring in packages_no_hash
                
                # quick way to search packages
                on_anaconda_channel = False
                simple_name = get_simplified_name(name_no_hashstring)
                if simple_name in pkgs_dict:
                    if name_no_hashstring in pkgs_dict[simple_name]:
                        on_anaconda_channel = True
                
                meta = MetaData(recipe_dir)
                meta.full_build_path = path_to_built_package
                meta.build_name = name_on_anaconda
                meta.build_command = build_cmd
                if on_anaconda_channel:
                    metas_not_to_build.append(meta)
                else:
                    metas_to_build.append(meta)

            logger.info('{:<8} | {:<5} | {:<5} | {}'.format(
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
    test_deps = {}
    logger.debug("Building dependency graph for %s libraries", len(metas))

    for meta in metas:
        name = meta.meta['package']['name']
        logger.debug('name=%s', name)
        build_deps[name] = sanitize_names(
            meta.meta.get('requirements', {}).get('build', []))
        logger.debug('build_deps=%s', build_deps)
        run_deps[name] = sanitize_names(
            meta.meta.get('requirements', {}).get('run', []))
        logger.debug('run_deps=%s', run_deps)
        test_deps[name] = sanitize_names(
            meta.meta.get('test', {}).get('requires', []))
        logger.debug('test_deps=%s', test_deps)
    # pdb.set_trace()
    # union = copy.deepcopy(build_deps)
    union = {k: set(build_deps.get(k, []) + run_deps.get(k, []) +
                    test_deps.get(k, []))
             for k in set(list(run_deps.keys()) + list(build_deps.keys()) +
                          list(test_deps.keys()))}
    # logger.debug()
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

    Notes
    -----
    copied from conda-build-all. Thanks @pelson!
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


def run_build(metas, username, token=None, upload=True, allow_failures=False):
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
    allow_failures : bool, optional

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
    logger.info("Build Order.")
    for meta in build_order:
        logger.info(meta.build_name)

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
        # need to run the build command with --output again or conda freaks out
        # stdout, stderr, returncode = Popen(build_command + ['--output'])
        # output the build command
        print("Build cmd: %s" % ' '.join(build_command))
        np = ''
        try:
            np_idx = build_command.index('--numpy')
        except ValueError:
            # --numpy is not in build_command
            pass
        else:
            # get the numpy version as the argument following the `--numpy`
            # flag
            np = build_command[np_idx+1]
        with env_var('CONDA_NPY', np):
            stdout, stderr, returncode = Popen(build_command)
        if returncode != 0:
            build_or_test_failed.append(build_name)
            message = ('\n\n========== STDOUT ==========\n'
                       '\n{}'
                       '\n\n========== STDERR ==========\n'
                       '\n{}'.format(pformat(stdout), pformat(stderr)))
            logger.error(message)
            #message_slack(message, username, is_error=True)
            if not allow_failures:
                sys.exit(1)
        if token and upload:
            print("UPLOAD START")
            cmd = UPLOAD_CMD + [full_build_path]
            cleaned_cmd = list(cmd)
            cleaned_cmd[2] = 'SCRUBBED'
            print("Upload command={}".format(cleaned_cmd))
            stdout, stderr, returncode = Popen(cmd)
            if returncode != 0:
                message = ('\n\n========== STDOUT ==========\n'
                           '\n{}'
                           '\n\n========== STDERR ==========\n'
                           '\n{}'.format(pformat(stdout), pformat(stderr)))
                logger.error(message)
                #message_slack(message, username, is_error=True)
                upload_failed.append(build_name)
                continue
            message_slack("Built and Uploaded {}".format(build_name), username)
            uploaded.append(build_name)
            continue

        no_token.append(build_name)

    return {
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
    global slack_channel
    global slack_api
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
        dest='python',
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
    # TODO Verify that `--site` actually works...
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
    p.add_argument(
        '--allow-failures', help=("Enable build.py to continue building conda "
                                  "packages if one of them fails"),
        default=False, action="store_true"
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
        default=slack_channel,
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
    args_dct['upload'] = not args_dct.pop('no_upload')
    args_dct['recipes_path'] = os.path.abspath(args.recipes_path)
    # set up slack integration
    slack_token = args_dct.pop('slack_token')
    slack_channel = args_dct.pop('slack_channel', slack_channel)
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

    print(args_dct)
    run(**args_dct)


def init_logging(log_file=None, loglevel=logging.INFO):
    if not log_file:
        log_dirname = os.path.join(os.path.expanduser('~'),
                                   'auto-build-logs')
        #os.makedirs(log_dirname, exist_ok=True)
        if not os.path.exists(log_dirname):
            os.makedirs(log_dirname)
        log_filename = time.strftime("%m.%d-%H.%M")
        log = os.path.join(log_dirname, log_filename)
    # set up logging
    print('Logging summary to %s' % log)
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(log)

    file_handler.setLevel(loglevel)
    stream_handler.setLevel(loglevel)
    logger.setLevel(loglevel)

    # FORMAT = "%(levelname)s | %(asctime)-15s | %(message)s"
    # file_handler.setFormatter(FORMAT)
    # stream_handler.setFormatter(FORMAT)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)


def message_slack(message, username, is_error=False):
    if slack_api is None:
        logger.info("Message to slack not posted. `slack_api` is None.")
    extra_info = (' to {} on {}'.format(username, anaconda_cli.domain))
    if is_error:
        file_handler, = [handler for handler in logger.handlers
                         if isinstance(handler, logging.FileHandler)]
        log_file_name = file_handler.stream.name
        extra_info += (
            '\n\ntarget anaconda username: {}'
            '\n\ntarget anaconda url: {}'
            '\n\nos.uname(): {}'
            '\n\nsys.version: {}'
            '\n\nlog file: {}'
            ''.format(username,
                      anaconda_cli.domain,
                      os.uname(),
                      sys.version,
                      log_file_name))

    message += extra_info
    logger.info("Sending the following message to slack")
    logger.info(message)
    slack_api.chat.post_message(slack_channel, message)


def run(recipes_path, python, site, username, numpy, token=None,
        upload=True, allow_failures=False,
        slack_channel=None):
    """
    Run the build for all recipes listed in recipes_path

    Parameters
    ----------
    recipes_path : str
        Folder that contains conda recipes
    python : iterable
        Iterable of python versions to build conda packages for
    site : str
        Anaconda server API url.
    username : str
        The username to check for packages and to upload built packages to
    numpy : iterable
        Iterable of numpy versions to build conda packages for
    token : str, optional
        Token used to authenticate against `site` so that packages can be
        uploaded. If no token is provided, os.environ['BINSTAR_TOKEN'] will be
        looked for. If that is not set, this script will likely error out.
    upload : bool, optional
        False: Don't upload built packages.
        Defaults to True
    allow_failures : bool, optional
        True: Continue building packages after one has failed.
        Defaults to False
    slack_channel : str, optional
        Slack channel to post to. Defaults to 'bob-the-builder'
    """
    # check to make sure that the recipes_path exists
    if not os.path.exists(recipes_path):
        logger.error("The recipes_path: '%s' does not exist." % recipes_path)
        sys.exit(1)
    # just disable binstar uploading whenever this script is running.
    print('Disabling binstar upload. If you want to turn it back on, '
          'execute: `conda config --set binstar_upload true`')
    set_binstar_upload(False)
    global anaconda_cli
    anaconda_cli = get_anaconda_cli(token, site)
    if numpy is None:
        numpy = os.environ.get("CONDA_NPY", DEFAULT_NP_VER)
        if not isinstance(numpy, list):
            numpy = [numpy]
    # get all file names that are in the channel I am interested in
    packages = get_file_names_on_anaconda_channel(username, anaconda_cli)

    metas_to_build, metas_to_skip = decide_what_to_build(
        recipes_path, python, packages, numpy)
    if metas_to_build == []:
        print('No recipes to build!. Exiting 0')
        sys.exit(0)

    # Run the actual build
    try:
        results = run_build(metas_to_build, username, token=token,
                            upload=upload, allow_failures=allow_failures)
        results['alreadybuilt'] = sorted([skip.build_name
                                          for skip in metas_to_skip])
    except Exception as e:
        tb = traceback.format_exc()
        message = ("Major error encountered in attempt to build\n{}\n{}"
                   "".format(tb, e))
        logger.error(message)
        message_slack(message, username, is_error=True)
        # exit with a failed status code
        sys.exit(1)
    else:
        logger.info("Build summary")
        logger.info('Expected {} packages'.format(len(metas_to_build)))
        num_builds = {k: len(v) for k, v in results.items()}
        logger.info('Got {} packages.'.format(
            sum([n for n in num_builds.values()])))
        logger.info('Breakdown is as follows')
        for k, v in num_builds.items():
            logger.info('section: {:<25}. number build: {}'.format(k, v))
        if results['build_or_test_failed']:
            message = ("Some packages failed to build\n{}"
                       "\n{}".format(pformat(results['build_or_test_failed'])))
            logger.error(message)
            message_slack(message, username, is_error=True)
        if results['no_token']:
            logger.error("No anaconda token. Cannot upload these packages")
            logger.error(pformat(results['no_token']))
        if results['upload_failed']:
            message = ('Upload failed for these packages'
                       '\n{}'.format(pformat(results['upload_failed'])))
            logger.error(message)
            message_slack(message, username, is_error=True)
        if results['alreadybuilt']:
            logger.info('Packages that already exist in {}'.format(username))
            logger.info(pformat(results['alreadybuilt']))
        if results['uploaded']:
            message = ('Packages that were built and uploaded to the {} user '
                       'on {}\n{}'.format(username, anaconda_cli.domain,
                                          pformat(results['uploaded'])))
            logger.info(message)

        if results['upload_failed'] or results['build_or_test_failed']:
            # exit with a failed status code
            sys.exit(1)

if __name__ == "__main__":
    cli()
