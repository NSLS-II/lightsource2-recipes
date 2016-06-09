#!/bin/bash

ACTIVATE=$PREFIX/etc/conda/activate.d/db-env-vars.sh
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/db-env-vars.sh
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d

# set up
echo "# metadatastore configuration
# installed by nslsii_dev_configuration
# DO NOT EDIT
export MDS_HOST=localhost
export MDS_DATABASE=datastore-dev
export MDS_PORT=27017
export MDS_TIMEZONE=US/Eastern
" > $ACTIVATE

echo "# filestore configuration
# installed by nslsii_dev_configuration
# DO NOT EDIT
export FS_HOST=localhost
export FS_DATABASE=filestore-dev
export FS_PORT=27017
" >> $ACTIVATE

echo "#metadataclient configuration
# installed by nslsii_dev_configuration
# DO NOT EDIT
export MDC_HOST=localhost
export MDC_PORT=7770
export MDC_PROTOCOL=http
export MDC_TIMEZONE=\"US/Eastern\"
" >> $ACTIVATE

echo "unset MDS_HOST
unset MDS_DATABASE
unset MDS_PORT
unset MDS_TIMEZONE
unset FS_HOST
unset FS_DATABASE
unset FS_PORT
unset MDC_HOST
unset MDC_PORT
unset MDC_PROTOCOL
unset MDC_DATABASE
" > $DEACTIVATE


