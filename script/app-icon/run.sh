#!/bin/bash

set -e

if [[ -z "${MLC_ICON_SRC_PATH}" ]]; then
    echo "ICON is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/icon"
    exit 1
fi

SRC="${MLC_ICON_SRC_PATH}"
echo "Using user-provided ICON tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
