#!/bin/bash

function cmake() {
${MLC_CMAKE_BIN_WITH_PATH} $@
}

export CC=${MLC_C_COMPILER_WITH_PATH}
export CXX=${MLC_CXX_COMPILER_WITH_PATH}

export -f cmake
export HEXAGON_TOOLS_DIR=${MLC_HEXAGON_TOOLS_INSTALLED_DIR}/clang+llvm-15.0.5-cross-hexagon-unknown-linux-musl/x86_64-linux-gnu

mkdir -p src
rsync -avz --exclude=.git  ${MLC_QAIC_COMPUTE_SDK_PATH}/ src/
cd src

if [[ ${MLC_CLEAN_BUILD} == "yes" ]]; then
  rm -rf build
fi

./scripts/build.sh --${MLC_QAIC_COMPUTE_SDK_INSTALL_MODE} --install
test $? -eq 0 || exit $?

cd -
