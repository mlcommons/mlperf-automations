#!/bin/bash
icx_bin=${MLC_ICX_BIN_WITH_PATH}
echo "${icx_bin} --version"

${icx_bin} --version > tmp-ver.out
test $? -eq 0 || exit $?
