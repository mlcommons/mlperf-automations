#!/bin/bash

if [[ -n ${MLC_LLVM_FORCE_VERSION} ]]; then
  exit 0
fi

clang_bin=${MLC_LLVM_CLANG_BIN_WITH_PATH}
${clang_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
