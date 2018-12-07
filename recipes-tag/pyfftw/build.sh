#!/usr/bin/env bash

export C_INCLUDE_PATH=$PREFIX/include  # required as fftw3.h installed here

# define STATIC_FFTW_DIR so the patched setup.py will statically link FFTW
export STATIC_FFTW_DIR=$PREFIX/lib

# define PYFFTW_USE_PTHREADS so that we do not use the openmp version
export PYFFTW_USE_PTHREADS=1

if [[ `uname` == 'Linux' ]]; then
    # -Bsymbolic link flag to ensure MKL FFT routines don't shadow FFTW ones.
    # see:  https://github.com/pyFFTW/pyFFTW/issues/40
    export CFLAGS="$CFLAGS -Wl,-Bsymbolic"
fi

$PYTHON -m pip install . --no-deps --ignore-installed -vvv
