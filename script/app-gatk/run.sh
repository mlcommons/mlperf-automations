#!/bin/bash

set -e

if [[ -z "${MLC_GATK_SRC_PATH}" ]]; then
    echo "GATK source not found!"
    exit 1
fi

SRC="${MLC_GATK_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"
# Requires a JDK; builds a runnable jar.
./gradlew installDist

echo "GATK build step completed."
