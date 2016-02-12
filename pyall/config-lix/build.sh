#!/bin/bash

mkdir -p $PREFIX/etc
ETC=$PREFIX/etc


# set up
echo "# metadatastore configuration
# installed by lix_configuration
# DO NOT EDIT
host: xf16id-ws1
database: datastore
port: 27017
timezone: US/Eastern
" > $ETC/metadatastore.yml

echo "# filestore configuration
# installed by lix_configuration
# DO NOT EDIT
host: xf16id-ws1
database: filestore
port: 27017
" > $ETC/filestore.yml



# clean up after self
unset ETC
