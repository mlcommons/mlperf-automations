#!/bin/bash

set -e

if [[ -z "${MLC_NEKTAR_SRC_PATH}" ]]; then
    echo "Nektar++ source not found!"
    exit 1
fi

SRC="${MLC_NEKTAR_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
git config --global --add safe.directory "${SRC}" || true
# Boost >= 1.89 ships no boost_system library (header-only); requiring it makes Nektar build its bundled Boost 1.71, which fails with new GCC.
sed -i -E '/SET\(NEEDED_BOOST_LIBS/s/ system( |\))/\1/' cmake/ThirdPartyBoost.cmake
# Bundled ThirdParty CMakeLists declare cmake_minimum_required < 3.5, which CMake 4 rejects.
export CMAKE_POLICY_VERSION_MINIMUM=3.5
# Bundled Boost 1.71 does not bootstrap with modern GCC; always use system Boost.
rm -rf build
cmake -S . -B build \
    -DTHIRDPARTY_BUILD_BOOST=OFF \
    -DNEKTAR_USE_SCOTCH=OFF \
    -DNEKTAR_USE_SYSTEM_BLAS_LAPACK=OFF -DNEKTAR_USE_OPENBLAS=ON \
    -DNEKTAR_BUILD_SOLVERS=OFF -DNEKTAR_BUILD_DEMOS=ON \
    -DNEKTAR_BUILD_TESTS=OFF -DNEKTAR_BUILD_UNIT_TESTS=OFF \
    -DNEKTAR_BUILD_UTILITIES=OFF -DNEKTAR_USE_MPI=OFF
cmake --build build -j"${CORES}"

if ! ls build/library/LibUtilities/libLibUtilities.so* >/dev/null 2>&1; then
    echo "Nektar++ library not built"
    exit 1
fi

echo "Nektar++ build step completed."
