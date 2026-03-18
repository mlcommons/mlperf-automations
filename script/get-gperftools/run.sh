#!/bin/bash

set -e
CUR=$PWD
install_dir=$CUR/install
mkdir -p install_dir

#Add your run commands here...
# run "$MLC_RUN_CMD"
cd ${MLC_GPERFTOOLS_SRC_PATH}
./autogen.sh
./configure --prefix=$install_dir
make -j${MLC_HOST_CPU_PHYSICAL_CORES_PER_SOCKET}
make install
