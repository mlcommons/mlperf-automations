#!/bin/bash

CUR_DIR=$PWD

mkdir -p install
mkdir -p build

INSTALL_DIR="${CUR_DIR}/install"

echo "******************************************************"

cd build

if [ "${MLC_MLPERF_AUTOMOTIVE_LOADGEN_DOWNLOAD}" == "YES" ]; then
    export MLC_MLPERF_AUTOMOTIVE_SOURCE="${MLC_EXTRACT_EXTRACTED_PATH}"
fi


if [ -z "${MLC_MLPERF_AUTOMOTIVE_SOURCE}" ]; then
   echo "Error: env MLC_MLPERF_AUTOMOTIVE_SOURCE is not defined - something is wrong with script automation!"
   exit 1
fi

cmake \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
     "${MLC_MLPERF_AUTOMOTIVE_SOURCE}/loadgen" \
     -DPYTHON_EXECUTABLE:FILEPATH="${MLC_PYTHON_BIN_WITH_PATH}" -B .
test $? -eq 0 || exit $?

echo "******************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}

cmake --build . --target install -j "${MLC_MAKE_CORES}"
test $? -eq 0 || exit $?

# Clean build directory (too large)
cd "${CUR_DIR}"
if [[ $MLC_MLPERF_AUTOMOTIVE_LOADGEN_BUILD_CLEAN == "yes" ]]; then
  rm -rf build
fi


cd "${MLC_MLPERF_AUTOMOTIVE_SOURCE}/loadgen"
${MLC_PYTHON_BIN_WITH_PATH} -m pip install . --target="${MLPERF_AUTOMOTIVE_PYTHON_SITE_BASE}"
test $? -eq 0 || exit $?

# Clean the built wheel
#find . -name 'mlcommons_loadgen*.whl' | xargs rm

echo "******************************************************"
echo "Loadgen is built and installed to ${INSTALL_DIR} ..."
