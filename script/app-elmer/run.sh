#!/bin/bash

set -e

if [[ -z "${MLC_ELMER_SRC_PATH}" ]]; then
    echo "Elmer source not found!"
    exit 1
fi

SRC="${MLC_ELMER_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
# Old bundled CMakeLists declare cmake_minimum_required < 3.5, which CMake 4 rejects.
export CMAKE_POLICY_VERSION_MINIMUM=3.5
# GCC 14+/15 reject legacy C in matc (K&R prototypes, implicit declarations); restore old behaviour.
cmake -B build -DWITH_MPI=FALSE -DWITH_ELMERGUI=FALSE -DWITH_ElmerIce=FALSE \
    -DCMAKE_INSTALL_PREFIX="${SRC}/install" \
    -DCMAKE_C_FLAGS="-std=gnu17 -Wno-error=implicit-function-declaration -Wno-error=incompatible-pointer-types -Wno-error=int-conversion ${CFLAGS}"
# Build the core solver only; some optional modules do not compile
# with gfortran >= 13 (DO-loop index passed by reference).
cmake --build build --target Solver_TGT -- -j"${CORES}"

if ! find build -name ElmerSolver -type f | grep -q .; then
    echo "Elmer binary not built"
    exit 1
fi

echo "Elmer build step completed."
