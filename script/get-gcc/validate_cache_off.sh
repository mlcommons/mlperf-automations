#!/bin/bash

if [[ -n "$MLC_GCC_DIR_PATH" && -e "$MLC_GCC_DIR_PATH" ]]; then
    if [[ "$(realpath "$MLC_GCC_DIR_PATH")" != "$(realpath "$MLC_GCC_INSTALLED_PATH")" ]]; then
	echo "$MLC_GCC_DIR_PATH" has changed from the cached entry. Invalidating the cache entry.
        exit 1
    fi
fi

${MLC_GCC_INSTALLED_PATH}/bin/gcc --version > tmp-ver.out
test $? -eq 0 || exit $?
