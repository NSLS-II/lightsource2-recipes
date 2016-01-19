#!/bin/bash

mkdir -p $PREFIX/etc
ETC=$PREFIX/etc


# set up
echo "# metadatastore configuration
# installed by amx_configuration
# DO NOT EDIT
host: lsbr-dev
database: datastore
port: 27017
timezone: US/Eastern
" > $ETC/metadatastore.yml

echo "# filestore configuration
# installed by amx_configuration
# DO NOT EDIT
host: lsbr-dev
database: filestore
port: 27017
" > $ETC/filestore.yml



# clean up after self
unset ETC
