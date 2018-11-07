import os
import datetime
import docker
from pathlib import Path


def run_container(*, pkg_name,
                  pythons=('3.5', '3.6', '3.7'),
                  numpy_versions=('1.14',), upload=True):
    """
    Run a Docker container with supplied commands.

    Parameters
    ----------
    pkg_name : str
        the name of a package to build
    pythons : tuple, optional
        versions of Python to build the package for
    numpy_versions : tuple, optional
        versions of NumPy to build the package for
    """

    # Hard-code it for now to avoid typing it every time.
    # See https://github.com/NSLS-II/lightsource2-recipes/pull/390
    # for the discussion.
    docker_image='mrakitin/debian-with-miniconda:latest'

    # Date-time vars
    start_time = datetime.datetime.now()
    timestamp = datetime.datetime.strftime(start_time, '%Y%m%d%H%M%S')

    # Tokens/env vars
    slack_channel = os.getenv('SLACK_CHANNEL')
    upload_channel = os.getenv('UPLOAD_CHANNEL')
    binstar_token = os.getenv('BINSTAR_TOKEN')
    slack_token = os.getenv('SLACK_TOKEN')

    # Docker run options
    container_name = f'{pkg_name}-{timestamp}'
    pythons_str = ' '.join(pythons)
    numpy_str = ' '.join(numpy_versions)
    command = ['./repo/scripts/build.py',
               f' /repo/recipes-tag/{pkg_name}',
               f'-u {upload_channel}',
               f'--python {pythons_str}',
               f'--numpy {numpy_str}',
               f'--token {binstar_token}',
               f'--slack-channel {slack_channel}',
               f'--slack-token {slack_token}',
               '--allow-failures']
    if not upload:
        command.append('--no-upload')

    command = ' '.join(command)
    host_dir = str(Path.cwd().parents[0])
    guest_dir = '/repo'
    volumes = {host_dir: {'bind': guest_dir, 'mode': 'rw'}}

    print(f'Package name: {pkg_name}')
    print(f'Running the docker container: {container_name}\n')

    # Run Docker container
    docker_client = docker.from_env()
    container = docker_client.containers.run(docker_image,
                                          name=container_name,
                                          command=f'sh -c "{command}"',
                                          remove=False,
                                          stdout=True,
                                          stderr=True,
                                          volumes=volumes,
                                          detach=True)
    return container
