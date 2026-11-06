#!/bin/bash

set -e

if [[ -z "${MLC_MADGRAPH_SRC_PATH}" ]]; then
    echo "MadGraph5_aMC@NLO source not found!"
    exit 1
fi

SRC="${MLC_MADGRAPH_SRC_PATH}"
CORES="${MLC_HOST_CPU_TOTAL_PHYSICAL_CORES:-$(nproc)}"

cd "${SRC}"
python3 ./bin/mg5_aMC --version

echo "MadGraph5_aMC@NLO build step completed."
