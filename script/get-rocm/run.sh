#!/bin/bash

dir="${MLC_ROMLC_BIN_WITH_PATH%/*}/.."
version_file="${dir}/.info/version"

if [ -f "${version_file}" ]; then
    cat "${version_file}" > tmp-ver.out
    test $? -eq 0 || exit 1
elif [[ "${MLC_ROCM_BUILD_FROM_SRC}" == "yes" ]]; then
    # Source build: get version from clang --version output
    clang_bin="${MLC_ROMLC_BIN_WITH_PATH%/*}/clang"
    if [ -f "${clang_bin}" ]; then
        ${clang_bin} --version 2>&1 | head -1 | sed 's/.*version[ ]*//' | sed 's/[^0-9.].*//' > tmp-ver.out
    else
        echo "${MLC_VERSION}" > tmp-ver.out
    fi
    test $? -eq 0 || exit 1
else
    # Fallback: try rocminfo output
    ${MLC_ROMLC_BIN_WITH_PATH} 2>/dev/null | grep "Runtime Version" | head -1 | sed 's/.*: *//' > tmp-ver.out
    test $? -eq 0 || exit 1
fi
