# TODO: git clone submodule
# TODO: detect CUDA, MPI, and FFTW. See below --- 
# For CUDA, three issues: 1. If users want to run the GPU version, CUDA
# driver and toolkit must exist. The latter might be taken care of by conda, 
# but users must handle the former. 2. Conda has no up-to-date CuPy, and 
# users are encouraged to pip install a pre-built one based on the toolkit
# version, which makes the automation a bit more difficult. 3. User may only 
# need the CPU version, then we don't need to touch anything GPU-related!
#
# For MPI (and mpi4py), the problem is to build mpi4py on top of whatever
# MPI in the system. Conda is unable to do a customized build, and it's 
# better to install a specified MPI first (either from Conda or by oneself,
# if, say, cuda-aware MPI is needed), and then pip install mpi4py.
#
# Currently this script assumes 1. CuPy is either not needed or installed 
# separately, and 2. "conda install mpi4py" works. Obviously we need to 
# polish this when more beamlines need this package...

$PYTHON -m pip install . --no-deps --ignore-installed -vv
