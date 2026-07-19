#!/bin/bash

CUR_DIR=$PWD

echo "***********************************************************"
MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES}}
MLC_MAKE_CORES=${MLC_MAKE_CORES:-2}
MLC_WGET_URL=https://www.openssl.org/source/openssl-${MLC_VERSION}g.tar.gz
wget -nc ${MLC_WGET_URL}
test $? -eq 0 || exit 1
tar -xzf openssl-${MLC_VERSION}g.tar.gz && cd openssl-${MLC_VERSION}g
test $? -eq 0 || exit 1
mkdir -p install
./config --prefix=`pwd`/install
make -j${MLC_MAKE_CORES}
test $? -eq 0 || exit 1
make install
