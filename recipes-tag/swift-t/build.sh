#!/bin/bash

install -d $PREFIX/bin
install -d $PREFIX/etc
install -d $PREFIX/lib
install -d $PREFIX/scripts
install -d $PREFIX/swift-t

build_dir='dev/build/'

cd ${build_dir}
bash init-settings.sh
# sed 's;SWIFT_T_PREFIX=/tmp/swift-t-install;SWIFT_T_PREFIX='"$PREFIX"'/swift-t;' -i swift-t-settings.sh
# sed 's;ENABLE_PYTHON=0;ENABLE_PYTHON=1;' -i swift-t-settings.sh
# sed 's;PYTHON_EXE="";PYTHON_EXE="'"$PYTHON"'";' -i swift-t-settings.sh

bash build-swift-t.sh

# Setup symlinks for utilities
### BIN ###
cd $PREFIX/bin
for file in stc swift-t helpers.zsh; do
    ln -sv ../swift-t/stc/bin/$file .
done
for file in turbine; do
    ln -sv ../swift-t/turbine/bin/$file .
done

### ETC ###
cd $PREFIX/etc
for file in stc-config.sh turbine-version.txt; do
    ln -sv ../swift-t/stc/etc/$file .
done
ln -sv ../swift-t/turbine/etc/version.txt .

### LIB ###
cd $PREFIX/lib
ln -sv ../swift-t/stc/lib/*.jar .
# A workaround for a missing library
ln -sv libmpi.so libmpi.so.20

### SCRIPTS ###
cd $PREFIX/scripts
for file in turbine-config.sh; do
    ln -sv ../swift-t/turbine/scripts/$file .
done

