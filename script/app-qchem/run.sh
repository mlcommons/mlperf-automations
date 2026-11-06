#!/bin/bash

set -e

if [[ -z "${MLC_QCHEM_SRC_PATH}" ]]; then
    echo "Q-Chem is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/qchem"
    exit 1
fi

SRC="${MLC_QCHEM_SRC_PATH}"
echo "Using user-provided Q-Chem tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
