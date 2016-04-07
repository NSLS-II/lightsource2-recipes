#!/bin/bash
pkg_name=`basename $RECIPE_DIR`
py.test -vrxs `dirname \`python -c "import $pkg_name; print($pkg_name.__file__)"\``
