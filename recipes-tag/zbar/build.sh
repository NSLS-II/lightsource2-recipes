./configure --prefix=$PREFIX --disable-video --without-imagemagick --without-gtk --without-qt --without-python
make
make check
make install
