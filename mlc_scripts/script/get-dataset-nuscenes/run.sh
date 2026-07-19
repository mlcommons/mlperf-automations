#!/bin/bash

#MLC Script location: ${MLC_TMP_CURRENT_SCRIPT_PATH}

#To export any variable
#echo "VARIABLE_NAME=VARIABLE_VALUE" >>tmp-run-env.out

#${MLC_PYTHON_BIN_WITH_PATH} contains the path to python binary if "get,python" is added as a dependency

if [[ "$MLC_DOWNLOAD_MODE" != "dry" && "$MLC_TMP_REQUIRE_DOWNLOAD" = "true" ]]; then
  cd "${MLC_DATASET_NUSCENES_PATH}" || exit
  for f in *.tar.gz; do 
    tar -xzvf "$f" || { echo "Failed to extract $f"; exit 1; }
  done
  cd "${MLC_DATASET_NUSCENES_PATH}/nuscenes" || exit
  for f in *.tar.gz; do 
    tar -xzvf "$f" || { echo "Failed to extract $f"; exit 1; }
  done
  cd - || exit
fi