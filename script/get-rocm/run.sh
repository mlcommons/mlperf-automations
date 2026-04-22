#!/bin/bash

dir="${MLC_ROMLC_BIN_WITH_PATH%/*}/.."
version_file="${dir}/.info/version"

if [ -f "${version_file}" ]; then
    cat "${version_file}" > tmp-ver.out
    test $? -eq 0 || exit 1
else
    # Fallback: try rocminfo output
    ${MLC_ROMLC_BIN_WITH_PATH} 2>/dev/null | grep "Runtime Version" | head -1 | sed 's/.*: *//' > tmp-ver.out
    test $? -eq 0 || exit 1
fi
