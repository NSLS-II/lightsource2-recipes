d=$(python -c 'from __future__ import print_function; import distutils.sysconfig as s; print(s.get_python_lib())')
srw_path='env/work/srw_python'
rm -fv ${srw_path}/*.so
make all
(
    cd ${srw_path}
    install -m 644 {srwl,uti}*.py srwlpy*.so "$d"
)

