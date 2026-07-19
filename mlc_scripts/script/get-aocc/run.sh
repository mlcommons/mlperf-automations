#!/bin/bash

if [[ -n ${MLC_AOCC_FORCE_VERSION} ]]; then
  exit 0
fi

aocc_bin=${MLC_AOCC_BIN_WITH_PATH}
echo "${aocc_bin} --version"

${aocc_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
