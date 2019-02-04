# copied and pasted by Leo Fang from the following commit:
# https://github.com/conda-forge/mpich-feedstock/blob/1ee1a927c03fd9653313c1cdd79bea87ef5ef16a/recipe/build.sh

#!/bin/bash

# configure balks if F90 is defined
# with a fatal deprecation message pointing to FC
unset F90 F77

# remove --as-needed, which causes problems for downstream builds,
# seen in failures in petsc, slepc, and hdf5 at least
export LDFLAGS="${LDFLAGS/-Wl,--as-needed/}"

# avoid absolute-paths in compilers
export CC=$(basename "$CC")
export CXX=$(basename "$CXX")
export FC=$(basename "$FC")

# from anaconda recipe, not sure if it matters
export FCFLAGS="$FFLAGS"

# avoid recording flags in compilers
# See Compiler Flags section of MPICH readme
export MPICHLIB_CFLAGS=$CFLAGS
unset CFLAGS
export MPICHLIB_CXXFLAGS=$CXXFLAGS
unset CXXFLAGS
export MPICHLIB_LDFLAGS=$LDFLAGS
unset LDFLAGS
export MPICHLIB_FFLAGS=$FFLAGS
unset FFLAGS
export MPICHLIB_FCFLAGS=$FCFLAGS
unset FCFLAGS

# set some specific flags that we *do* want recorded in the compilers
# only the bare minimum of prefix-awareness here
export CFLAGS="-I$PREFIX/include"
export CXXFLAGS="-I$PREFIX/include"
export FFLAGS="-I$PREFIX/include"
export LDFLAGS="-L$PREFIX/lib -Wl,-rpath,$PREFIX/lib"

export LIBRARY_PATH="$PREFIX/lib"

./configure --prefix=$PREFIX \
            --disable-dependency-tracking \
            --enable-cxx \
            --enable-fortran

make -j"${CPU_COUNT:-1}"
make install
