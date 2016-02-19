autoreconf -i
./configure --enable-python --disable-perl --disable-java \
	    --disable-fortran2003 --disable-lua --prefix=$PREFIX
make -j 4
make install
