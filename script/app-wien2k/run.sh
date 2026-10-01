#!/bin/bash

set -e

if [[ -z "${MLC_WIEN2K_SRC_PATH}" ]]; then
    echo "WIEN2k is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/wien2k"
    exit 1
fi

SRC="${MLC_WIEN2K_SRC_PATH}"
echo "Using user-provided WIEN2k tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
