#!/bin/bash

set -e

if [[ -z "${MLC_GAUSSIAN_SRC_PATH}" ]]; then
    echo "Gaussian is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/gaussian"
    exit 1
fi

SRC="${MLC_GAUSSIAN_SRC_PATH}"
echo "Using user-provided Gaussian tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
