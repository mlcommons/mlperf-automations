#!/bin/bash

if [[ "$MLC_DOWNLOAD_MODE" != "dry" && "$MLC_TMP_REQUIRE_DOWNLOAD" = "true" ]]; then
  cd "${MLC_PREPROCESSED_DATASET_NUSCENES_PATH}/${MLC_DATASET_NUSCENES_TAR_FILENAME}" || exit
  for f in *.tar.gz; do 
    tar -xzvf "$f" || { echo "Failed to extract $f"; exit 1; }
  done
  cd - || exit
fi