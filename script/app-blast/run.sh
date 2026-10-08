#!/bin/bash

set -e

if [[ -z "${MLC_BLAST_SRC_PATH}" ]]; then
    echo "BLAST+ source not found!"
    exit 1
fi

SRC="${MLC_BLAST_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

# The NCBI C++ Toolkit configure lives at the repo root. Restrict to the BLAST
# project to limit the (still very large) build.
cd "${SRC}"
./configure --without-debug --with-mt \
    --with-projects=scripts/projects/blast/project.lst \
    --prefix="${INSTALL_DIR}"

# configure creates a versioned build tree (e.g. GCC*-Release*/build).
BUILD_DIR="$(find "${SRC}" -maxdepth 1 -type d -name '*-Release*' | head -1)"
make -C "${BUILD_DIR}/build" -j${CORES} all_r
make -C "${BUILD_DIR}/build" install || true

if [[ ! -x "${INSTALL_DIR}/bin/blastn" ]]; then
    echo "BLAST+ binary (blastn) not built"
    exit 1
fi

echo "BLAST+ built successfully."
