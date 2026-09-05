#!/bin/bash

set -e

VISUALS_DIR="${MLC_INFRAGRAPH_VISUALS_DIR_PATH}"
if [[ "${MLC_INFRAGRAPH_SKIP_VISUALIZE}" == "True" ]]; then
    VISUALS_DIR=""
fi

# infragraph is driven through its Python API rather than its console script:
# get,generic-python-lib installs it into the MLC-selected interpreter, whose
# bin directory is not necessarily on PATH.
"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/build_infragraph.py" \
    --input-dir "${MLC_INFRAGRAPH_INPUT_DIR_PATH}" \
    --output "${MLC_INFRAGRAPH_FILE_PATH}" \
    --output-yaml "${MLC_INFRAGRAPH_YAML_FILE_PATH}" \
    --name "${MLC_INFRAGRAPH_NAME}" \
    --visuals-dir "${VISUALS_DIR}"
