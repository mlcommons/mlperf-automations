#!/bin/bash
uprof_bin=${MLC_UPROF_BIN_WITH_PATH}
echo "${uprof_bin} --version"

${uprof_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
