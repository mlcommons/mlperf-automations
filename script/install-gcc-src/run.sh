#!/bin/bash

CUR_DIR=$PWD

echo "******************************************************"

if [ ! -d "src" ]; then
  echo "Cloning GCC from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT}..."
  git clone -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} src
  if [ "${?}" != "0" ]; then exit 1; fi
fi

mkdir -p install
mkdir -p build

INSTALL_DIR="${CUR_DIR}/install"

echo "******************************************************"
cd src
./contrib/download_prerequisites
cd ../build

../src/configure --prefix="${INSTALL_DIR}" --with-gcc-major-version-only --disable-multilib

if [ "${?}" != "0" ]; then exit 1; fi

echo "******************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}

make -j${MLC_MAKE_CORES}
if [ "${?}" != "0" ]; then exit 1; fi
make install
if [ "${?}" != "0" ]; then exit 1; fi

# Clean build directory (too large)
cd ${CUR_DIR}
rm -rf build

echo "******************************************************"
echo "GCC was built and installed to ${INSTALL_DIR} ..."
