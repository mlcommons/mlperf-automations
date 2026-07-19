#!/bin/bash

# Create an isolated virtual environment for the inference-endpoint package so
# its heavy pinned dependencies do not collide with the MLC host Python.

VENV_DIR="${MLC_MLPERF_ENDPOINTS_VENV_PATH}"
VENV_PYTHON="${MLC_MLPERF_ENDPOINTS_PYTHON_BIN}"
SRC="${MLC_MLPERF_INFERENCE_ENDPOINTS_SOURCE}"

echo ""
echo "Creating virtual environment at ${VENV_DIR}"
"${MLC_PYTHON_BIN_WITH_PATH}" -m venv "${VENV_DIR}"
test $? -eq 0 || exit 1

echo ""
echo "Upgrading pip in the virtual environment"
"${VENV_PYTHON}" -m pip install --quiet --upgrade pip
test $? -eq 0 || exit 1

echo ""
echo "Installing inference-endpoint from ${SRC}"
"${VENV_PYTHON}" -m pip install "${SRC}"
test $? -eq 0 || exit 1

echo ""
echo "Verifying the inference-endpoint installation"
"${VENV_PYTHON}" -c "import inference_endpoint; print('inference-endpoint import OK')"
test $? -eq 0 || exit 1
