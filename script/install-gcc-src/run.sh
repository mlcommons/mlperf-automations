#!/bin/bash

CUR_DIR=$PWD

echo "******************************************************"

echo ${MLC_GCC_SRC_REPO_PATH}

if [ ! -d "src" ]; then
  cp -r ${MLC_GCC_SRC_REPO_PATH} src
  test $? -eq 0 || exit $?
fi

rm -rf install
rm -rf build

mkdir -p install
mkdir -p build

INSTALL_DIR="${CUR_DIR}/install"

echo "******************************************************"
cd src
./contrib/download_prerequisites
cd ../build


cmd="../src/configure --prefix="${INSTALL_DIR}" ${MLC_GCC_TARGET_STRING} ${MLC_GCC_HOST_STRING} ${MLC_GCC_BUILD_STRING} ${MLC_GCC_SYSROOT_STRING} ${MLC_GCC_EXTRA_CONFIGURE_STRING}  --with-gcc-major-version-only"
echo $cmd
eval $cmd

test $? -eq 0 || exit $?

echo "******************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}

make -j${MLC_MAKE_CORES}
test $? -eq 0 || exit $?

make install
test $? -eq 0 || exit $?

# Clean build directory (too large)
cd ${CUR_DIR}
rm -rf build

echo "******************************************************"
echo "GCC was built and installed to ${INSTALL_DIR} ..."
