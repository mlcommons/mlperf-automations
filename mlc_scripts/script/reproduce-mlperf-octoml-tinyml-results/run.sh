#!/bin/bash

CUR_DIR=$PWD

code=${MLC_MICROTVM_SOURCE}/closed/OctoML/code
model=${MLC_TINY_MODEL:-ad}
microtvm_variant=${MLC_MICROTVM_VARIANT}
board=${MLC_TINY_BOARD:-NUCLEO_L4R5ZI}
source=${code}/${microtvm_variant}

path_suffix="${board}/${model}"
cmake_src=${source}/${path_suffix}
build_path=${CUR_DIR}/${path_suffix}
echo "MLC_TINY_BUILD_DIR=${build_path}/build" > tmp-run-env.out
mkdir -p ${build_path}
cd ${build_path}
binary_path=${build_path}/build/zephyr/zephyr.elf
if [ -f "${binary_path}" ] && [ "${MLC_RECREATE_BINARY}" != "True" ]; then
  echo "ELF binary existing at ${binary_path}. Skipping regeneration."
  cd build
else
  rm -rf build
  mkdir -p build
  cd build
  MLC_MAKE_CORES=${MLC_MAKE_CORES:-${MLC_HOST_CPU_TOTAL_CORES:-2}}
  cmake ${cmake_src}
  test $? -eq 0 || exit 1
  make -j${MLC_MAKE_CORES}
  test $? -eq 0 || exit 1
  cd ../
  echo "ELF binary created at ${build_path}/build/zephyr/zephyr.elf"
fi
