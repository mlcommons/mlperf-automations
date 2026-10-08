#!/bin/bash

set -e

if [[ -z "${MLC_HOOMD_SRC_PATH}" ]]; then
    echo "HOOMD-blue source not found!"
    exit 1
fi

SRC="${MLC_HOOMD_SRC_PATH}"
INSTALL_DIR="${SRC}/install"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"

cd "${SRC}"

# HOOMD v7 needs pybind11 >= 2.12 (newer than the distro package) and numpy.
"${PYTHON}" -m venv "${INSTALL_DIR}/venv"
VPY="${INSTALL_DIR}/venv/bin/python"
"${VPY}" -m pip install --upgrade pip pybind11 numpy
PYBIND_DIR="$("${VPY}" -m pybind11 --cmakedir)"

# HOOMD-blue is a CMake project (not pip-installable). Build the CPU version.
cmake -B build -S . -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
    -DENABLE_MPI=off -DENABLE_GPU=off -DBUILD_TESTING=off \
    -DPython_EXECUTABLE="${VPY}" -Dpybind11_DIR="${PYBIND_DIR}"
cmake --build build -j${CORES}
cmake --install build

echo "HOOMD-blue build step completed."
