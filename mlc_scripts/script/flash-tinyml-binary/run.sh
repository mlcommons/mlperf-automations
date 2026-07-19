#!/bin/bash

build_dir=${MLC_TINY_BUILD_DIR}
cmd="cd ${MLC_ZEPHYR_DIR}"
echo $cmd
eval $cmd
cmd="west flash --build-dir ${build_dir}"
echo $cmd
eval $cmd
test $? -eq 0 || exit 1

