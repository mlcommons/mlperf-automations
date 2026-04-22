#!/bin/bash

amdclang_bin=${MLC_AMDCLANG_BIN_WITH_PATH}
${amdclang_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
