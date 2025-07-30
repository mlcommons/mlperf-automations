#!/bin/bash

#MLC Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

#To export any variable
#echo "VARIABLE_NAME=VARIABLE_VALUE" >>tmp-run-env.out

#${MLC_PYTHON_BIN_WITH_PATH} contains the path to python binary if "get,python" is added as a dependency

if [[ "$MLC_DOWNLOAD_MODE" != "dry" && "$MLC_TMP_REQUIRE_DOWNLOAD" = "yes" ]]; then
  cd "${MLC_DATASET_WAYMO_PATH}/training" || exit
  for f in *.tar.gz; do tar -xzvf "$f"; done
  cd - || exit
fi