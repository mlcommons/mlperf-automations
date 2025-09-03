#!/bin/bash
gcc_bin=${MLC_GCC_BIN_WITH_PATH}
echo "${gcc_bin} --version"

${gcc_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?

cat tmp-ver.out
