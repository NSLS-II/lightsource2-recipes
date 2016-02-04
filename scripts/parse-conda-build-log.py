
from __future__ import (unicode_literals, absolute_import, division,
                        print_function)
import six
from collections import defaultdict
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
    TARGET_LINE = '/tmp/staged-recipes'
    full_path = os.path.abspath(path_to_log)
    output = []
    package_name = ''
    with open(full_path, 'r') as f:
        for line in f.readlines():
            # remove white space and newline characters
            line = line.strip()
            if line.startswith(TARGET_LINE):
                # always have to treat the first package differently...
                if package_name != '':
                    yield package_name, output
                package_name = os.path.split(line)[1]
                output = []
            else:
                output.append(line)

def parse_conda_build(lines_iterable):
    """
    Group the output from conda-build into a dictionary keyed on
    'init', 'build', 'test' and 'upload'

    Returns
    -------
    dict
        dict keyed on 'init', 'build', 'test', 'upload'. Not all keys are
        guaranteed to be present. Protip: If one of the keys is missing, it is
        probably because there was an error...
    """
    from collections import defaultdict
    bundle = []
    end_section = iter(["BUILD START", "TEST START", "TEST END", "no end to this section"])
    next_line_might_be_test = False
    init = True
    build = False
    test = False
    key = 'init'
    ret = defaultdict(list)
    for line in lines_iterable:
        ret[key].append(line)
        # init
        if init:
            if line.startswith("BUILD START"):
                init = False
                build = True
                key = 'build'
        # build
        if build:
            if line.startswith("BUILD END"):
                next_line_might_be_test = True
                build = False
        # determine if test or upload comes next
        if next_line_might_be_test:
            if line.startswith("TEST START"):
                test = True
                key = 'test'
            else:
                key = 'upload'
        # test
        if test:
            if line.startswith("TEST END"):
                test = False
    return ret


if __name__ == "__main__":
    log = 'build.log'
    gen = read_log_from_script(log)
    for name, lines in gen:
        parsed = parse_conda_build(lines)
        print('{:20s} -- {}'.format(name, list(parsed.keys())))