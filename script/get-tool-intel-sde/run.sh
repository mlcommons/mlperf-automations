#!/bin/bash
sde_bin=${MLC_INTEL_SDE_BIN_WITH_PATH}
echo "${sde_bin} --version"

${sde_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
