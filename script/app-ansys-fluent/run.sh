#!/bin/bash

set -e

if [[ -z "${MLC_ANSYS_FLUENT_SRC_PATH}" ]]; then
    echo "Ansys Fluent is proprietary and cannot be downloaded automatically."
    echo "Provide a licensed source/install tree with: --src=/path/to/ansys-fluent"
    exit 1
fi

SRC="${MLC_ANSYS_FLUENT_SRC_PATH}"
echo "Using user-provided Ansys Fluent tree at: ${SRC}"
echo "Follow the vendor's build/run instructions for your licensed distribution."
