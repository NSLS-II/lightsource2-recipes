#!/bin/bash


export FS_HOST=localhost
export FS_DATABASE='FS_test'
export FS_PORT=27017

python -c "import filestore"
python -c "import filestore.api"
python -c "import filestore.commands"
python -c "import filestore.conf"
python -c "import filestore.core"
python -c "import filestore.file_writers"
python -c "import filestore.fs"
python -c "import filestore.handlers_base"
python -c "import filestore.handlers"
python -c "import filestore.path_only_handlers"
python -c "import filestore.retrieve"