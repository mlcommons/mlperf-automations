#!/bin/bash

set -e

if [[ -z "${MLC_CANTERA_SRC_PATH}" ]]; then
    echo "Cantera source not found!"
    exit 1
fi

SRC="${MLC_CANTERA_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true

# Build the core C++ library only (no Python/Fortran interface), reusing the
# system Eigen/SUNDIALS/yaml-cpp/fmt packages.
scons build -j"${CORES}" python_package=n f90_interface=n \
    system_eigen=y system_sundials=y system_yamlcpp=y system_fmt=y

if ! ls build/lib/libcantera_shared.so* >/dev/null 2>&1; then
    echo "Cantera library not built"
    exit 1
fi

echo "Cantera build step completed."
