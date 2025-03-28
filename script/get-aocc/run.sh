#!/bin/bash
aocc_bin=${MLC_AOCC_BIN_WITH_PATH}
echo "${aocc_bin} --version"

${aocc_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
