#!/bin/bash

set -e

if [[ -z "${MLC_CALCULIX_SRC_PATH}" ]]; then
    echo "CalculiX is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/calculix"
    exit 1
fi

SRC="${MLC_CALCULIX_SRC_PATH}"
echo "Using user-provided CalculiX tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
