#!/bin/bash

set -e

if [[ -z "${MLC_WW3_SRC_PATH}" ]]; then
    echo "WaveWatch III source not found!"
    exit 1
fi

SRC="${MLC_WW3_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}/model"
./bin/w3_setup . -c gnu -s Ifremer1 || true
./bin/w3_make

echo "WaveWatch III build step completed."
