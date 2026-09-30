#!/bin/bash

set -e

if [[ -z "${MLC_FUN3D_SRC_PATH}" ]]; then
    echo "FUN3D is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/fun3d"
    exit 1
fi

SRC="${MLC_FUN3D_SRC_PATH}"
echo "Using user-provided FUN3D tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
