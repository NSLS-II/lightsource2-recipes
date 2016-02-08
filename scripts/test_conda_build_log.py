import pytest
import log_parser

import os


@pytest.fixture
def parsed_log():
    logname = os.path.join(os.path.split(os.path.abspath(__file__))[0],
                           'build.log')
    gen = list(log_parser.read_log_from_script(logname))
    parsed = {built_name: log_parser.parse_conda_build(lines)
              for name, built_name, lines in gen}
    return parsed


def test_parse_conda_build(parsed_log):
    # make sure that we have at least one thing that was parsed
    assert len(parsed_log) >= 1

def test_parse_init(parsed_log):
    # make sure we are getting the build command out of every single entry
    for pkg_name, parsed in parsed_log.items():
        parsed_init = log_parser.parse_init(parsed['init'])
        assert 'build_command' in parsed_init
        assert 'err' in parsed_init

def test_parse_build(parsed_log):
    # make sure we are getting either an error or the build string out of the
    # build section
    for pkg_name, parsed in parsed_log.items():
        if 'build' not in parsed:
            # not all packages will successfully build
            continue
        # if there is a build section, then parse it
        parsed_build = log_parser.parse_build(parsed['build'])
        if parsed_build['built_name'] == 'failed':
            assert parsed_build['error'] != []
        else:
            assert parsed_build['error'] == []

