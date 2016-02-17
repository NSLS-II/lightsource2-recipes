import sys
import traceback
import subprocess
import os
import time
import logging


def get_file_names_on_anaconda_channel(username, channel='main'):
    return set([f['basename']
               for f in cli.show_channel('main', username)['files']])


def determine_build_name(path_to_recipe, *conda_build_args):
    if conda_build_args is None:
        conda_build_args = []
    cmd = ['conda', 'build', path_to_recipe, '--output']
    cmd.extend(conda_build_args)
    ret = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    ret = ret.decode().strip().split('\n')
    if len(ret) > 1:
        # Then this is the first time we are getting the build name and conda
        # has to check out the source. Call it a second time and you get the full
        # path to the file that will be spit out by conda-build
        return determine_build_name(path_to_recipe, *conda_build_args)
    cmd.remove('--output')
    return ret[0], cmd


def run_build(recipes_path, log_filename):
    logging.basicConfig(filename=log_filename, level=logging.DEBUG)

    # figure out build names
    build_names = []
    print("Determining package build names...")
    for folder in sorted(os.listdir(recipes_folder)):
        for pyver in ['2.7', '3.4', '3.5']:
            path_to_built_package, build_cmd = determine_build_name(
                os.path.join(recipes_folder, folder), '--python', pyver)
            print(name)
            name_on_anaconda = os.sep.join(name.split(os.sep)[-2:])
            build_names.append(path_to_built_package, name_on_anaconda,
                               build_cmd)
    # check anaconda to see if they already exist

    # split into 'already_exist' and 'need_to_build'
    lightsource2_packages = get_file_names_on_anaconda_channel('lightsource2-dev')
    build_package = []
    dont_build_package = []
    for name, cmd in build_names:
        if name in lightsource2_packages:
            dont_build_package.append((name, cmd))
        else:
            build_package.append((name, cmd))

    # log the names of those that already exist
    logger.info("%s / %s packages already exist on %s" % (
            len(dont_build_package),
            len(dont_build_package) + len(build_package),
            username))
    if dont_build_package:
        for pkg, cmd in dont_build_package:
            print(pkg)
    else:
        logger.info("No packages exist on %s" % username)

    # log the names of those that need to build
    logger.info("%s / %s packages do not exist on %s" % (
            len(build_package),
            len(dont_build_package) + len(build_package),
            username))
    if build_package:
        for pkg, cmd in build_package:
            logger.info(pkg)
    else:
        logger.info("No packages to be built.")



    # build all the packages that need to be built

    # for each package
    for pkg, cmd in build_names:
        # output the package build name
        logger.info("Building: %s"% pkg)
        # output the build command
        logger.info("Build cmd: %s" % cmd)
        # capture the output with subprocess.Popen
        try:
            ret = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   stdout=subprocess.PIPE)
        except Exception as e:
            # ALL exceptions that occur in the subprocess command
            logger.error('Exception summary: %s' % e.strerror)
            logger.error('Full exception start')
            logger.error(traceback.format_exc)
            logger.error('Full exception stop')
        # decode and capture stdout and stderr
        stdout = ret.stdout.read().decode().strip().split('\n')
        stderr = ret.stderr.read().decode().strip().split('\n')
        # log stdout as 'info'
        logging.info(stdout)
        # log stderr as 'error'
        logging.error(warning)


if __name__ == "__main__":
    def print_usage():
        print("\nUsage:\n\tpython dev-build.py /path/to/dev/recipes")

    args = sys.argv
    if len(args) != 2:
        print("Error!")
        print("The command \"%s\" is invalid" % ' '.join(args))
        print("You supplied %s arguments. I am expecting 2." % len(args))
        print_usage()
        sys.exit(2)

    recipes_path = args[1]
    if not os.path.exists(recipes_path):
        print("Error!")
        print("The path '%s' does not exist." % recipes_path)
        print("Please supply the path to the dev recipes as the first "
              "argument to dev-build.py")
        print_usage()
        sys.exit(3)

    full_recipes_path = os.path.abspath(recipes_path)

    dev_log_folder = os.path.join(os.path.expanduser('~'),
                                  'auto-build-logs', 'dev')
    os.makedirs(dev_log_folder, exist_ok=True)
    log_name = time.strftime("%m.%d-%H.%M")
    dev_log = os.path.join(dev_log_folder, log_name)
    print('Logging output to %s' % dev_log)


