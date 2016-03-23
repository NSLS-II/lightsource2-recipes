#!/usr/bin/env python,

from setuptools import setup, find_packages
import versioneer
setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='nsls2-auto-builder',
    description='toolset for analyzing automated conda package building at NSLS2',
    author='Eric Dill',
    author_email='edill@bnl.gov',
    url='https://github.com/ericdill/conda_build_utils',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['click', 'yaml', 'pyyaml'],
    entry_points="""
        [console_scripts]
        devbuild=nsls2_build_tools.build:cli
    """

)
