#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer
setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='nsls2-auto-builder',
    description='toolset for analyzing automated conda package building at NSLS2',
    author='Eric Dill',
    author_email='edilL@bnl.gov',
    url='https://github.com/NSLS-II/nsls2-auto-builder',
    packages=find_packages(),
    include_package_data=True,
    long_description='See https://github.com/freeman-lab/pim'
)
