# make all
d=$(python -c 'from __future__ import print_function; import distutils.sysconfig as s; print(s.get_python_lib())')
(
    cd env/work/srw_python
    install -m 644 {srwl,uti}*.py srwlpy.so "$d"
)

