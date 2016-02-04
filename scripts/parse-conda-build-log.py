
from __future__ import (unicode_literals, absolute_import, division,
                        print_function)
import six

import os

def read_log_from_script(path_to_log):
    """
    Parse the log that is output from the `dev-build` script

    Parameters
    ----------
    path_to_log : str
        The path to the log file that results from `bash dev-build > log 2>&1`

    Yields
    ------
    package : str
        The name of the package that is being built
    output : list
        The lines that were output for the build/test/upload of `package`
    """
    BUILD_START_LINE = '/tmp/staged-recipes'
    PACKAGE_NAME_LINE = '# $ anaconda upload '
    full_path = os.path.abspath(path_to_log)
    output = []
    package_name = ''
    with open(full_path, 'r') as f:
        for line in f.readlines():
            # remove white space and newline characters
            line = line.strip()
            if line.startswith(PACKAGE_NAME_LINE):
                # split the line on the whitespace that looks something like:
                # "# $ anaconda upload /tmp/root/ramdisk/mc/conda-bld/linux-64/album-v0.0.2_py35.tar.bz2"
                built_package_path = line.split()[-1]
                # remove the folder path
                built_package_name = os.path.split(built_package_path)[-1]
                # trim the '.tar.bz2'
                built_name = built_package_name[:-8]
            if line.startswith(BUILD_START_LINE):
                # always have to treat the first package differently...
                if package_name != '':
                    yield package_name, built_name, output
                package_name = os.path.split(line)[1]
                built_name = '%s-build-name-not-found' % package_name
                output = []
            else:
                output.append(line)

    yield package_name, built_name, output


def parse_conda_build(lines_iterable):
    """
    Group the output from conda-build into
    - 'build_init'
    - 'build'
    - 'test'
    - 'upload'
    """
    from collections import defaultdict
    bundle = []
    next_line_might_be_test = False
    init = True
    build = False
    test = False
    key = 'init'
    ret = []
    for line in lines_iterable:
        bundle.append(line)
        # init
        if init:
            if line.startswith("BUILD START"):
                ret.append((key, bundle))
                bundle = []
                init = False
                build = True
                key = 'build'
        # build
        if build:
            if line.startswith("BUILD END"):
                next_line_might_be_test = True
                build = False
                continue
        # determine if test or upload comes next
        if next_line_might_be_test:
            next_line_might_be_test = False
            ret.append((key, bundle))
            bundle = []
            if line.startswith("TEST START"):
                test = True
                key = 'test'
            else:
                key = 'upload'
        # test
        if test:
            if line.startswith("TEST END"):
                ret.append((key, bundle))
                bundle = []
                test = False
                key='upload'

    if bundle:
        ret.append((key, bundle))
    return ret


if __name__ == "__main__":
    log = 'build.log'
    gen = list(read_log_from_script(log))
    parsed = {built_name: parse_conda_build(lines) for name, built_name, lines in gen}
    width = max([len(name) for name in parsed.keys()])
    for name, groups in parsed.items():
        print(('{:%ds} -- {}' % width).format(name, [key for key, bundle in groups]))