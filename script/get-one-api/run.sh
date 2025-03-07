#!/bin/bash
oneapi_bin=${MLC_ONEAPI_BIN_WITH_PATH}
echo "${oneapi_bin} version"

${oneapi_bin} version > tmp-ver.out
test $? -eq 0 || exit 1

cat tmp-ver.out
