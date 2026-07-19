#!/bin/bash

# Drives the multi-point submission orchestration. All configuration is passed
# via MLC_MLPERF_ENDPOINTS_SUB_* environment variables (see customize.py).
# PRISM_USER_API_TOKEN must be exported for the (non-dry-run) runs/submissions
# API calls.

"${MLC_PYTHON_BIN_WITH_PATH}" "${MLC_TMP_CURRENT_SCRIPT_PATH}/src/orchestrate.py"
test $? -eq 0 || exit $?
