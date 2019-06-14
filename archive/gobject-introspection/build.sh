#! /bin/bash

set -e
IFS=$' \t\n' # workaround for conda 4.2.13+toolchain bug

export PKG_CONFIG_LIBDIR=$PREFIX/lib/pkgconfig:$PREFIX/share/pkgconfig

configure_args=(
    --prefix=$PREFIX
    --disable-dependency-tracking
    --with-cairo
)

if [ $PY3K = 1 ] ; then
    # Work around a weakness in AM_CHECK_PYTHON_HEADERS. It finds the Python
    # interpreter and calls it $PYTHON, then runs "$PYTHON-config --includes"
    # to get the needed C #include flags. On Unixy platforms, conda-build sets
    # $PYTHON to "$PREFIX/bin/python", so the configure script adopts that
    # value. But in Python 3 situations, Anaconda does not provide
    # "$PREFIX/bin/python-config", so configure fails to figure out where the
    # headers live. Anaconda does provide "python3-config", though, so if we
    # just tweak the executable name, things work.
    configure_args+=(--with-python=python3)
fi

if [ $(uname) = Darwin ] ; then
    LDFLAGS="$LDFLAGS -Wl,-rpath,$PREFIX/lib"
else
    LDFLAGS="$LDFLAGS -Wl,-rpath-link,$PREFIX/lib"
fi

./configure "${configure_args[@]}" || { cat config.log ; exit 1 ; }
make -j$CPU_COUNT
make install

rm -f $PREFIX/lib/libgirepository-*.a $PREFIX/lib/libgirepository-*.la
