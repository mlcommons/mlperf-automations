#!/bin/bash

set -e

if [[ -z "${MLC_KRATOS_SRC_PATH}" ]]; then
    echo "Kratos source not found!"
    exit 1
fi

SRC="${MLC_KRATOS_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYBIN="${MLC_PYTHON_BIN_WITH_PATH:-$(command -v python3)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DUSE_MPI=OFF \
    -DKRATOS_BUILD_TESTING=OFF -DPYTHON_EXECUTABLE="${PYBIN}"
# Build the core library (full application set is very large).
cmake --build build -j"${CORES}" --target KratosCore

if ! find build -name "libKratosCore*" | grep -q .; then
    echo "Kratos core library not built"
    exit 1
fi

echo "Kratos build step completed."
