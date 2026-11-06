#!/bin/bash

set -e

if [[ -z "${MLC_PSI4_SRC_PATH}" ]]; then
    echo "Psi4 source not found!"
    exit 1
fi

SRC="${MLC_PSI4_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

# Psi4's CMake needs a Python with NumPy; provide one in a venv.
"${PYTHON}" -m venv "${INSTALL_DIR}/venv"
VPY="${INSTALL_DIR}/venv/bin/python"
"${VPY}" -m pip install --upgrade pip numpy setuptools

# CMake superbuild fetches and builds the external dependencies.
cmake -S . -B build -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DPython_EXECUTABLE="${VPY}"
# First build pass; psi4 v1.9.1 bundles externals whose versioneer.py uses
# configparser.SafeConfigParser, removed in Python >= 3.12.
cmake --build build -j${CORES} || true
find build -name versioneer.py -exec sed -i \
    's/configparser.SafeConfigParser/configparser.ConfigParser/g; s/SafeConfigParser()/ConfigParser()/g; s/\.readfp(/.read_file(/g' {} + 2>/dev/null || true
cmake --build build -j${CORES}

echo "Psi4 build step completed."
