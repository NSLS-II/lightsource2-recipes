d=$(python -c 'from __future__ import print_function; import distutils.sysconfig as s; print(s.get_python_lib())')

srw_path='env/work/srw_python'
so_basename='srwlpy'

rm -fv ${srw_path}/${so_basename}*.so

# Get and compile fftw2 lib & compile SRW *.so lib:
make all

(
    cd ${srw_path}

    # This file is generated in Python 2.7:
    so_file="${so_basename}.so"

    # This file is generated in Python 3.6, but the file above is also generated:
    cpython_so_file=$(ls -1 ${so_basename}*.so 2>/dev/null | grep -v ${so_file})

    if [ ! -z "${cpython_so_file}" ]; then
        so=${cpython_so_file}
    else
        so=${so_file}
    fi
    install -m 644 {srwl,uti}*.py ${so} "$d"
)

