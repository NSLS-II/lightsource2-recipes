#!/bin/bash

ETC=$PREFIX/etc
ACTIVATE=$PREFIX/etc/conda/activate.d/db-env-vars.sh
DEACTIVATE=$PREFIX/etc/conda/deactivate.d/db-env-vars.sh
mkdir -p $PREFIX/etc/conda/activate.d
mkdir -p $PREFIX/etc/conda/deactivate.d

MDS_HOST=xf10id-ca1
MDS_DATABASE=datastore
MDS_PORT=27017
MDS_TIMEZONE=US/Eastern
FS_HOST=xf10id-ca1
FS_DATABASE=filestore
FS_PORT=27017
MDC_HOST=xf10id-ca1
MDC_PORT=7770
MDC_PROTOCOL=http
MDC_TIMEZONE=US/Eastern

# set up
echo "# metadatastore configuration
# installed by ixs
# DO NOT EDIT
host: $MDS_HOST
database: $MDS_DATABASE
port: $MDS_PORT
timezone: $MDS_TIMEZONE
" > $ETC/metadatastore.yml

echo "# filestore configuration
# installed by ixs
# DO NOT EDIT
host: $FS_HOST
database: $FS_DATABASE
port: $FS_PORT
" > $ETC/filestore.yml

echo "# metadataclient configuration
# installed by ixs
# DO NOT EDIT
mdc_host: $MDC_HOST
mdc_port: $MDC_PORT
mdc_protocol: $MDC_PROTOCOL
mdc_timezone: $MDC_TIMEZONE
" > $ETC/metadataclient.yml

# set up
echo "# metadatastore configuration
# installed by ixs
# DO NOT EDIT
export MDS_HOST=$MDS_HOST
export MDS_DATABASE=$MDS_DATABASE
export MDS_PORT=$MDS_PORT
export MDS_TIMEZONE=$MDS_TIMEZONE
" > $ACTIVATE

echo "# filestore configuration
# installed by ixs
# DO NOT EDIT
export FS_HOST=$FS_HOST
export FS_DATABASE=$FS_DATABASE
export FS_PORT=$FS_PORT
" >> $ACTIVATE

echo "#metadataclient configuration
# installed by ixs
# DO NOT EDIT
export MDC_HOST=$MDC_HOST
export MDC_PORT=$MDC_PORT
export MDC_PROTOCOL=$MDC_PROTOCOL
export MDC_TIMEZONE=$MDC_TIMEZONE
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