#!/usr/bin/env python
"""
Script that generates the configuration information for NSLS-II from a yaml
file and jinja templates
"""
# conda execute
# env:
#   - python
#   - pyyaml
#   - jinja2
import copy
import os
import shutil

import yaml
from jinja2 import Environment, FileSystemLoader

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
template_package = os.path.join(THIS_DIR, 'template-package')

jinja_env = Environment(loader=FileSystemLoader(template_package))
configuration_yaml = yaml.load(open(os.path.join(THIS_DIR,
                                                 'config.yaml'), 'r').read())

default_configuration = configuration_yaml.pop('default')
LIB_NAMES = ['MDS', 'FS', 'MDC']


for package_name, package_contents in configuration_yaml.items():
    config = copy.deepcopy(default_configuration)
    config['package_name'] = package_name
    config['version'] = package_contents.get('version', config['version'])
    host = package_contents.get('host')
    # update each of the packages
    for lib in LIB_NAMES:
        if host:
            # allow easy setting of host for all the various services
            config[lib]['host'] = host
        for k, v in package_contents.get(lib, {}).items():
            config[lib][k] = v

    # render the package
    package_folder = os.path.join(THIS_DIR, package_name)
    print("package_folder={}".format(package_folder))
    try:
        os.mkdir(package_folder)
    except FileExistsError:
        # remove the folder and its contents
        shutil.rmtree(package_folder)
        os.mkdir(package_folder)
    # copy the unlink script to the target folder
    shutil.copy(os.path.join(template_package, 'pre-unlink.sh'),
                package_folder)

    # render the build script
    build_template = jinja_env.get_template('build.tmpl')
    build_sh = build_template.render(**config)
    # write the build script to disk
    with open(os.path.join(package_folder, 'build.sh'), 'w') as f:
        f.write(build_sh)

    # render the meta.yaml
    meta_template = jinja_env.get_template('meta.tmpl')
    env_vars = ['{}_{}'.format(lib_name, key.upper()) for lib_name in LIB_NAMES
                for key in config[lib_name].keys()]
    meta_yaml = meta_template.render(env_vars=env_vars, **config)
    with open(os.path.join(package_folder, 'meta.yaml'), 'w') as f:
        f.write(meta_yaml)

