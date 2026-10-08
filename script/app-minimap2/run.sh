#!/bin/bash

set -e

if [[ -z "${MLC_MINIMAP2_SRC_PATH}" ]]; then
    echo "minimap2 source not found!"
    exit 1
fi

SRC="${MLC_MINIMAP2_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
BIN_DIR="${INSTALL_DIR}/bin"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

echo "Building minimap2..."
echo "Source: ${SRC}"

cd "${SRC}"

echo "Building minimap2 with ${CORES} cores..."
make -j${CORES}

mkdir -p "${BIN_DIR}"
cp -f minimap2 "${BIN_DIR}/"

# Smoke test with the bundled tiny input
echo "Running minimap2 smoke test..."
"${BIN_DIR}/minimap2" -a \
    "${MLC_TMP_CURRENT_SCRIPT_PATH}/test/tiny.fa" \
    "${MLC_TMP_CURRENT_SCRIPT_PATH}/test/tiny.fa" > minimap2_smoke.sam

if ! grep -q "^@" minimap2_smoke.sam; then
    echo "Smoke test failed: no SAM header produced"
    exit 1
fi

echo "minimap2 built and smoke-tested successfully."
