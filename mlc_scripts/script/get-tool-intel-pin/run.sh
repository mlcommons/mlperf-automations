#!/bin/bash
pintool_bin=${MLC_INTEL_PINTOOL_BIN_WITH_PATH:-${MLC_INTEL_PINTOOL_DIR_PATH}/pin}
echo "${pintool_bin} -version"

${pintool_bin} -version > tmp-ver.out
test $? -eq 0 || exit $?
