#!/bin/bash

mkdir -p $PREFIX/etc
ETC=$PREFIX/etc


# set up
echo "# metadatastore configuration
# installed by csx2_configuration
# DO NOT EDIT
host: xf23id-broker
database: datastore-23id2
port: 27017
timezone: US/Eastern
" > $ETC/metadatastore.yml

echo "# filestore configuration
# installed by csx2_configuration
# DO NOT EDIT
host: xf23id-broker
database: filestore-23id2
port: 27017
" > $ETC/filestore.yml



# clean up after self
unset ETC
