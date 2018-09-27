import datetime
from dask.distributed import Client, LocalCluster


def new_ts():
    start_time = datetime.datetime.now()
    return datetime.datetime.strftime(start_time, '%Y%m%d%H%M%S')


if __name__ == '__main__':
    # List the packages to build here:
    packages = ['tomopy']

    cluster = LocalCluster(n_workers=8, threads_per_worker=1)
    print('\nCluster: {}\n'.format(cluster))

    client = Client(cluster)
    print('\nClient: {}\n'.format(client))

    '''
    packages = []
    import glob
    for p in sorted(glob.glob(str(Path.cwd().parents[0] / Path('recipes-tag/*')))):
        p = os.path.basename(p)
        print(p)
        packages.append(p)
    print(len(packages))
    '''

    statuses = []
    for p in packages:
        st = client.submit(run_container, pkg_name=p, pythons=('3.6', '3.7'),
                           numpy_versions=('1.14',),
                           key=f'{p}-{new_ts()}')
        statuses.append(st)
