#!/bin/bash

set -e

if [[ -z "${MLC_LS_DYNA_SRC_PATH}" ]]; then
    echo "LS-DYNA is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/ls-dyna"
    exit 1
fi

SRC="${MLC_LS_DYNA_SRC_PATH}"
echo "Using user-provided LS-DYNA tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
