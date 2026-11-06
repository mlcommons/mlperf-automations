#!/bin/bash

set -e

if [[ -z "${MLC_CASTEP_SRC_PATH}" ]]; then
    echo "CASTEP is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/castep"
    exit 1
fi

SRC="${MLC_CASTEP_SRC_PATH}"
echo "Using user-provided CASTEP tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
