#!/bin/bash


export MDS_HOST=localhost
export MDS_DATABASE='mds_test'
export MDS_PORT=27017
export MDS_TIMEZONE='US/EASTERN'

python -c "import metadatastore"
python -c "import metadatastore.api"
python -c "import metadatastore.commands"
python -c "import metadatastore.conf"
python -c "import metadatastore.examples"
python -c "import metadatastore.examples.sample_data"
python -c "import metadatastore.examples.sample_data.common"
python -c "import metadatastore.examples.sample_data.multisource_event"
python -c "import metadatastore.examples.sample_data.temperature_ramp"
