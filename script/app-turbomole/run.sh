#!/bin/bash

set -e

if [[ -z "${MLC_TURBOMOLE_SRC_PATH}" ]]; then
    echo "TURBOMOLE is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/turbomole"
    exit 1
fi

SRC="${MLC_TURBOMOLE_SRC_PATH}"
echo "Using user-provided TURBOMOLE tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
