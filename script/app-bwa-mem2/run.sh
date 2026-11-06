#!/bin/bash

set -e

if [[ -z "${MLC_BWA_MEM2_SRC_PATH}" ]]; then
    echo "bwa-mem2 source not found!"
    exit 1
fi

SRC="${MLC_BWA_MEM2_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
BIN_DIR="${INSTALL_DIR}/bin"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"

# bwa-mem2 defines its own __rdtsc() which clashes with the built-in intrinsic
# on GCC >= 11; restrict the custom definition to older GCC.
if [[ -f src/utils.h ]]; then
    sed -i 's/#if defined(__GNUC__) && !defined(__clang__)$/#if defined(__GNUC__) \&\& !defined(__clang__) \&\& (__GNUC__ < 11)/' src/utils.h
fi

echo "Building bwa-mem2 with ${CORES} cores..."
make -j${CORES}

mkdir -p "${BIN_DIR}"
cp -f bwa-mem2* "${BIN_DIR}/"

# Smoke test: index a tiny reference and align it to itself
echo "Running bwa-mem2 smoke test..."
WORK="$(pwd)/bwa_smoke"
rm -rf "${WORK}"
mkdir -p "${WORK}"
cp "${MLC_TMP_CURRENT_SCRIPT_PATH}/test/tiny.fa" "${WORK}/ref.fa"
cd "${WORK}"

"${BIN_DIR}/bwa-mem2" index ref.fa
"${BIN_DIR}/bwa-mem2" mem -t "${CORES}" ref.fa ref.fa > bwa_smoke.sam

if ! grep -q "^@SQ" bwa_smoke.sam; then
    echo "Smoke test failed: no SAM @SQ header produced"
    exit 1
fi

echo "bwa-mem2 built and smoke-tested successfully."
