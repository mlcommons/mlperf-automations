#!/bin/bash

set -e

if [[ -z "${MLC_BIGDFT_SRC_PATH}" ]]; then
    echo "BigDFT source not found!"
    exit 1
fi

SRC="${MLC_BIGDFT_SRC_PATH}"

# The BigDFT suite Installer must be run from a build directory that is
# separate from the source tree, and it fetches/builds a long chain of
# sub-packages (futile, PSolver, libABINIT, ...). Recipe is best-effort.
BUILD="${SRC}/../bigdft-build"
mkdir -p "${BUILD}"
cd "${BUILD}"
python3 "${SRC}/Installer.py" build -y

echo "BigDFT build step completed."
