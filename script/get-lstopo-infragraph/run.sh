#!/bin/bash

set -e
infragraph translate lstopo --input "${MLC_LSTOPO_XML_FILE_PATH}" --output "$(pwd)/dev.yaml"
echo "MLC_LSTOPO_INFRAGRAPH_FILE_PATH=$(pwd)/dev.yaml" > tmp-run-env.out
echo "dev.yaml written to $(pwd)/dev.yaml"

"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/annotate_sysinfo.py" \
    --sysinfo "${MLC_SINGLE_NODE_SYSTEM_INFO_FILE_PATH}" \
    --infragraph "$(pwd)/dev.yaml"