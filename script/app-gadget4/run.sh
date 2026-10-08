#!/bin/bash

set -e

if [[ -z "${MLC_GADGET4_SRC_PATH}" ]]; then
    echo "GADGET-4 source not found!"
    exit 1
fi

SRC="${MLC_GADGET4_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${SRC}"

# Use the built-in Generic-gcc system type (mpicxx + system library paths) and a
# minimal tree-gravity configuration bundled with this script.
export SYSTYPE="Generic-gcc"
cp -f "${MLC_TMP_CURRENT_SCRIPT_PATH}/test/Config.sh" Config.sh

# GADGET-4's build scripts invoke `python`; make sure it resolves to python3.
if ! command -v python >/dev/null 2>&1; then
    SHIM_DIR="$(mktemp -d)"
    ln -sf "$(command -v "${PYTHON}" || command -v python3)" "${SHIM_DIR}/python"
    export PATH="${SHIM_DIR}:${PATH}"
fi

# On Debian/Ubuntu the HDF5 headers/libs live under a 'serial' subdirectory that
# is not on the default search path; point the build at them when present.
if [[ -d /usr/include/hdf5/serial ]]; then
    export CPATH="/usr/include/hdf5/serial:${CPATH}"
fi
for d in /usr/lib/x86_64-linux-gnu/hdf5/serial /usr/lib/aarch64-linux-gnu/hdf5/serial; do
    [[ -d "$d" ]] && export LIBRARY_PATH="${d}:${LIBRARY_PATH}" && export LD_LIBRARY_PATH="${d}:${LD_LIBRARY_PATH}"
done

echo "Building GADGET-4 (SYSTYPE=${SYSTYPE}) with ${CORES} cores..."
make -j${CORES}

if [[ ! -x Gadget4 ]]; then
    echo "GADGET-4 binary (Gadget4) not built"
    exit 1
fi

echo "GADGET-4 built successfully."
