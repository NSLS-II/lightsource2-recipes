#!/bin/bash
# copied and pasted by Leo Fang from the following commit:
# https://github.com/conda-forge/mpich-feedstock/blob/1ee1a927c03fd9653313c1cdd79bea87ef5ef16a/recipe/run_test.sh

command -v mpichversion
mpichversion

command -v mpicc
mpicc -show

command -v mpicxx
mpicxx -show

command -v mpif90
mpif90 -show

command -v mpiexec

pushd tests

function mpi_exec() {
  # use pipes to avoid O_NONBLOCK issues on stdin, stdout
  mpiexec -launcher fork $@ 2>&1 </dev/null | cat
}

mpicc $CFLAGS $LDFLAGS helloworld.c -o helloworld_c
mpi_exec -n 4 ./helloworld_c

mpicxx $CXXFLAGS $LDFLAGS helloworld.cxx -o helloworld_cxx
mpi_exec -n 4 ./helloworld_cxx

mpif77 $FFLAGS $LDFLAGS helloworld.f -o helloworld_f
mpi_exec -n 4 ./helloworld_f

mpif90 $FFLAGS $LDFLAGS helloworld.f90 -o helloworld_f90
mpi_exec -n 4 ./helloworld_f90

popd
