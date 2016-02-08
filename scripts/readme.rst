Information gathered from conda-build output
--------------------------------------------
- PRE-BUILD

  - `build_command` : The build command that the conda building script executes
  - `err` : Any errors that are found in the pre-build section. Specifically
            looking for any line that starts with 'Error' or 'Traceback'

    - Specific errors that are caught in the test suite:

      - "Error: 'numpy x.x' requires external setting"

        - Covered by `test_parse_bad_yaml()`
        - log: `test_data/bad-yaml.log`

- BUILD

  - `built_name` : name of built package. Will be 'failed' if the build fails
  - `err` : Any errors that are found in the build section

    - Specific errors that are caught in the test suite

      - Error: Connection error: [SSL: CERTIFICATE_VERIFY_FAILED] certificate
        verify failed (_ssl.c:645):
        https://pypi.python.org/packages/source/t/tzlocal/tzlocal-1.1.2.zip'

        - log: `test_data/build.log`
        - packages that have this: tzlocal, readline, keyring, pymongo,
                                   humanize, hgtools, super_state_machine

      -  "subprocess.CalledProcessError: Command '['/usr/bin/git', 'checkout', "
         "'0.9.7']' returned non-zero exit status 1"

         - log: `test_data/build.log`
         - raised by slicerator

- TEST

  - `nothing_to_test` : If true, there was nothing in the test section of the
                        meta.yaml
  - `err` : Any errors that are found in the build section

    - Requirement listed in test requirements not found

      - Covered by `test_parse_bad_test_requires()`
      - log: `test_data/bad_import_requires.log`

    - Import failure

      - Covered by `test_parse_bad_test_import()`
      - log: `test_data/bad_import.log`

- UPLOAD
