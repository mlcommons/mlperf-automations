#!/bin/bash

set -e

if [[ -z "${MLC_NEMO_SRC_PATH}" ]]; then
    echo "NEMO is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/nemo"
    exit 1
fi

SRC="${MLC_NEMO_SRC_PATH}"
echo "Using user-provided NEMO tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
