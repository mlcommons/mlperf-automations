#!/bin/bash

set -e

if [[ -z "${MLC_AMBER_SRC_PATH}" ]]; then
    echo "AMBER is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/amber"
    exit 1
fi

SRC="${MLC_AMBER_SRC_PATH}"
echo "Using user-provided AMBER tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
