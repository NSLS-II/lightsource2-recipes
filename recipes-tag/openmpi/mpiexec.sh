#!/bin/bash
# copied and pasted by Leo Fang from the following commit:
# https://github.com/conda-forge/openmpi-feedstock/blob/1d6390794529ad80f5b3416fa2cb98882d1c95fa/recipe/mpiexec.sh

set -e
# pipe stdout, stderr through cat to avoid O_NONBLOCK issues
mpiexec --allow-run-as-root $@ 2>&1</dev/null | cat
