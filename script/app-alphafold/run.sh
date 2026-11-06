#!/bin/bash

set -e

if [[ -z "${MLC_ALPHAFOLD_SRC_PATH}" ]]; then
    echo "AlphaFold source not found!"
    exit 1
fi

SRC="${MLC_ALPHAFOLD_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
"${PYTHON}" -m venv "${INSTALL_DIR}"
"${INSTALL_DIR}/bin/pip" install --upgrade pip
"${INSTALL_DIR}/bin/pip" install -r requirements.txt
echo "Model parameters and genetic databases must be downloaded separately."

echo "AlphaFold build step completed."
