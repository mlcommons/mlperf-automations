#!/bin/bash

set -e

if [[ -z "${MLC_ATHENA_SRC_PATH}" ]]; then
    echo "Athena++ source not found!"
    exit 1
fi

SRC="${MLC_ATHENA_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"
PYTHON="${MLC_PYTHON_BIN_WITH_PATH:-python3}"
COMPILER_TAG="${MLC_COMPILER_FAMILY:-default}"
case "${COMPILER_TAG}" in
  oneapi) ATH_CXX=icpx ;;
  gcc|default) ATH_CXX=g++ ;;
  *) ATH_CXX=clang++ ;;
esac

cd "${SRC}"

echo "Configuring Athena++ (shock_tube problem)..."
"${PYTHON}" configure.py --prob=shock_tube --cxx "${ATH_CXX}"

echo "Building Athena++ with ${CORES} cores..."
make clean || true
make -j${CORES}

if [[ ! -x bin/athena ]]; then
    echo "Athena++ binary not built"
    exit 1
fi

# Smoke test: 1D Sod shock tube, limited to a few cycles
echo "Running Athena++ smoke test (Sod shock tube, 5 steps)..."
mkdir -p athena_smoke_out
./bin/athena -i inputs/hydro/athinput.sod time/nlim=5 -d athena_smoke_out

mkdir -p "bin-${COMPILER_TAG}" && cp bin/athena "bin-${COMPILER_TAG}/athena"
echo "Athena++ built and smoke-tested successfully."
