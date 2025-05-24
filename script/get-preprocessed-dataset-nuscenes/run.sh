#!/bin/bash

if [[ "$MLC_DOWNLOAD_MODE" != "dry" && "$MLC_TMP_REQUIRE_DOWNLOAD" = "yes" ]]; then
  cd "${MLC_PREPROCESSED_DATASET_NUSCENES_PATH}" || exit
  for f in *.tar.gz; do 
    tar -xzvf "$f" || { echo "Failed to extract $f"; exit 1; }
  done
  cd "${MLC_PREPROCESSED_DATASET_NUSCENES_ACC_CHECKER_MIN_FILES_PATH}" || exit
  for f in *.tar.gz; do 
    tar -xzvf "$f" || { echo "Failed to extract $f"; exit 1; }
  done
  cd - || exit
fi