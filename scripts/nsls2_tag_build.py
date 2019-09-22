import argparse
import datetime
import docker
import os


def run_container(*, pkg_name,
                  python_versions=('3.6', '3.7'), numpy_versions=('1.14',),
                  no_upload=False, remove=False, no_detach=False):
    """
    Run a Docker container with supplied commands.

    Parameters
    ----------
    pkg_name : str
        the name of a package to build
    python_versions : tuple, optional
        versions of Python to build the package with
    numpy_versions : tuple, optional
        versions of NumPy to build the package with
    no_upload : bool
        do not upload the built package
    remove : bool
        remove the container after execution
    no_detach : bool
        do not use a detached mode for execution
    """

    # Hard-code it for now to avoid typing it every time.
    # See https://github.com/NSLS-II/lightsource2-recipes/pull/390
    # for the discussion.
    docker_image='nsls2/debian-with-miniconda:v0.1.2'

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
    python_str = ' '.join(python_versions)
    numpy_str = ' '.join(numpy_versions)
    command = ['/repo/scripts/build.py',
               f' /repo/recipes-tag/{pkg_name}',
               f'-u {upload_channel}',
               f'--python {python_str}',
               f'--numpy {numpy_str}',
               f'--token {binstar_token}',
               f'--slack-channel {slack_channel}',
               f'--slack-token {slack_token}',
               '--allow-failures']
    if no_upload:
        command.append('--no-upload')

    command = ' '.join(command)
    host_dir = os.path.dirname(os.path.dirname(__file__))
    guest_dir = '/repo'
    volumes = {host_dir: {'bind': guest_dir, 'mode': 'rw'}}

    print(f'Package name: {pkg_name}')
    print(f'Running the docker container: {container_name}\n')

    # Run Docker container
    docker_client = docker.from_env()
    container = docker_client.containers.run(docker_image,
                                             name=container_name,
                                             command=f'sh -c "{command}"',
                                             remove=remove,
                                             stdout=True,
                                             stderr=True,
                                             volumes=volumes,
                                             detach=not no_detach)
    return container


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Build a package with docker-py')
    parser.add_argument('-n', '--pkg-names', dest='pkg_names', nargs='+',
                        type=str, required=True,
                        help='a list of names of packages to build')
    parser.add_argument('--python-versions', nargs='*', type=str,
                        dest='python_versions', default=['3.6', '3.7'],
                        help='versions of Python to build the package with')
    parser.add_argument('--numpy-versions', nargs='*', type=str,
                        dest='numpy_versions', default=['1.14'],
                        help='versions of NumPy to build the package with')
    parser.add_argument('--no-upload', action='store_true',
                        dest='no_upload',
                        help='do not upload the built package')
    parser.add_argument('-r', '--remove', action='store_true',
                        dest='remove',
                        help='remove the container after execution')
    parser.add_argument('--no-detach', action='store_true',
                        dest='no_detach',
                        help='do not use a detached mode for execution')
    
    args = parser.parse_args()

    pkg_names = args.pkg_names
    if not pkg_names:
        parser.print_help()
        parser.exit()

    kwargs = dict(vars(args))
    del kwargs['pkg_names']  # we don't want to pass it to run_container()

    print(f'The following packages will be built: {", ".join(pkg_names)}')
    
    containers = {}
    # Submit a building job
    for pkg_name in pkg_names:
        kwargs['pkg_name'] = pkg_name
        containers[pkg_name] = run_container(**kwargs)

    if len(containers) == 1:
        # Print the log to stdout
        for line in containers[pkg_names[0]].logs(stream=True):
            print(line.decode().strip())
