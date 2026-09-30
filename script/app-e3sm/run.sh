#!/bin/bash

set -e

if [[ -z "${MLC_E3SM_SRC_PATH}" ]]; then
    echo "E3SM source not found!"
    exit 1
fi

SRC="${MLC_E3SM_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
echo "E3SM is built through its CIME case workflow; see components/ and cime/."

echo "E3SM build step completed."
