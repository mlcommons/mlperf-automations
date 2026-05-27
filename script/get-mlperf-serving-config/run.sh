#!/bin/bash
# Runs locally on the serving node after remote_run teleports this script there.
# SSH transport is handled entirely by the parent script (get-mlperf-multi-node-system-info).

${MLC_PYTHON_BIN_WITH_PATH} "${MLC_TMP_CURRENT_SCRIPT_PATH}/parse.py" \
    --log-path "${MLC_MLPERF_SERVING_LOG_PATH:-}" \
    --out-file "${MLC_MLPERF_SERVING_CONFIG_JSON}"
