#!/bin/bash

set -e

if [[ -z "${MLC_ORCA_SRC_PATH}" ]]; then
    echo "ORCA is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/orca"
    exit 1
fi

SRC="${MLC_ORCA_SRC_PATH}"
echo "Using user-provided ORCA tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
