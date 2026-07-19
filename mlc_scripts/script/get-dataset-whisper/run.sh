#!/bin/bash

# exit on error
set -e
if [ "${MLC_TMP_DATASET_TYPE}" != "preprocessed" ]; then
  cd "${MLC_MLPERF_INFERENCE_SOURCE}"

  echo "==> Downloading Librispeech data..."
  ${MLC_PYTHON_BIN_WITH_PATH} "${MLC_TMP_UTILS_DIR}/download_librispeech.py" \
      "${MLC_TMP_UTILS_DIR}/inference_librispeech.csv" \
      "${MLC_TMP_LIBRISPEECH_DIR}" \
      -e "${MLC_TMP_DATA_DIR}"

  echo "==> Consolidating dev-clean and dev-other into dev-all..."
  mkdir -p "${MLC_TMP_LIBRISPEECH_DIR}/dev-all"
  cp -r "${MLC_TMP_LIBRISPEECH_DIR}/dev-clean/"* \
        "${MLC_TMP_LIBRISPEECH_DIR}/dev-other/"* \
        "${MLC_TMP_LIBRISPEECH_DIR}/dev-all/"

  echo "==> Converting FLAC to WAV and creating manifest..."
  ${MLC_PYTHON_BIN_WITH_PATH} "${MLC_TMP_UTILS_DIR}/convert_librispeech.py" \
     --input_dir "${MLC_TMP_LIBRISPEECH_DIR}/dev-all" \
     --dest_dir "${MLC_TMP_DATA_DIR}/dev-all" \
     --output_json "${MLC_TMP_DATA_DIR}/dev-all.json"
  
  echo "==> Repackaging samples into ~30s chunks..."
  ${MLC_PYTHON_BIN_WITH_PATH} "${MLC_TMP_UTILS_DIR}/repackage_librispeech.py" \
      --manifest "${MLC_TMP_DATA_DIR}/dev-all.json" \
      --data_dir "${MLC_TMP_DATA_DIR}" \
      --output_dir "${MLC_TMP_DATA_DIR}/dev-all-repack" \
      --output_json "${MLC_TMP_DATA_DIR}/dev-all-repack.json"

fi