#!/bin/bash

set -e

if [[ -z "${MLC_MESA_SRC_PATH}" ]]; then
    echo "MESA source not found!"
    exit 1
fi

SRC="${MLC_MESA_SRC_PATH}"

# MESA requires the prebuilt MESA SDK (a specific GCC/GFortran toolchain plus
# vendored libraries) to be installed and MESASDK_ROOT/MESA_DIR exported. It
# does not build with a stock system compiler. Recipe is best-effort.
cd "${SRC}"
export MESA_DIR="${SRC}"
./install

echo "MESA build step completed."
