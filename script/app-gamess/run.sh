#!/bin/bash

set -e

if [[ -z "${MLC_GAMESS_SRC_PATH}" ]]; then
    echo "GAMESS (US) is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/gamess"
    exit 1
fi

SRC="${MLC_GAMESS_SRC_PATH}"
echo "Using user-provided GAMESS (US) tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
