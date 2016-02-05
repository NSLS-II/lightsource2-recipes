import pytest
import log_parser


@pytest.fixture
def parsed_log():
    logname = 'build.log'
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

def test_parse_build(parsed_log):
    # make sure we are getting either an error or the build string out of the
    # build section
    for pkg_name, parsed in parsed_log.items():
        # not all packages will successfully build
        if 'build' not in parsed:
            continue
        parsed_build = log_parser.parse_build(parsed['build'])
        if parsed_build['built_name'] == 'failed':
            assert parsed_build['error'] != []
        else:
            assert parsed_build['error'] == []

