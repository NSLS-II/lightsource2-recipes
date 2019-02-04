# copied and pasted by Leo Fang from the following commit:
# https://github.com/conda-forge/mpi4py-feedstock/blob/ff2cc11800303988538b8ce3e9707ea97d5bdd2e/recipe/run_test.sh

export OMPI_MCA_plm=isolated
export OMPI_MCA_btl_vader_single_copy_mechanism=none
export OMPI_MCA_rmaps_base_oversubscribe=yes

python -c 'import mpi4py; from mpi4py import MPI; print(MPI.get_vendor()); print(MPI.Get_library_version())'
