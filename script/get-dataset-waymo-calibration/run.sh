if [[ "$MLC_DOWNLOAD_MODE" != "dry" && "$MLC_TMP_REQUIRE_DOWNLOAD" = "true" ]]; then
  cd "${MLC_DATASET_WAYMO_CALIBRATION_PATH}/testing" || exit
  for f in *.tar.gz; do tar -xzvf "$f"; done
  cd - || exit
fi