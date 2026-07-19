#!/bin/bash

# Install the endpoints-submission-cli (and bundled submission-checker) into a
# dedicated virtual environment, isolated from the MLC host Python.

VENV_DIR="${MLC_MLPERF_ENDPOINTS_CLI_VENV_PATH}"
VENV_PYTHON="${MLC_MLPERF_ENDPOINTS_CLI_PYTHON_BIN}"
TARGET="${MLC_MLPERF_ENDPOINTS_CLI_INSTALL_TARGET}"

echo ""
echo "Creating virtual environment at ${VENV_DIR}"
"${MLC_PYTHON_BIN_WITH_PATH}" -m venv "${VENV_DIR}"
test $? -eq 0 || exit 1

echo ""
echo "Upgrading pip in the virtual environment"
"${VENV_PYTHON}" -m pip install --quiet --upgrade pip
test $? -eq 0 || exit 1

echo ""
echo "Installing endpoints-submission-cli from ${TARGET}"
"${VENV_PYTHON}" -m pip install "${TARGET}"
test $? -eq 0 || exit 1

echo ""
echo "Verifying the endpoints-submission-cli installation"
"${VENV_PYTHON}" -m endpoints_submission_cli.main --help > /dev/null 2>&1 \
  || "${MLC_MLPERF_ENDPOINTS_CLI_VENV_PATH}/bin/endpoints-submission-cli" --help > /dev/null
test $? -eq 0 || exit 1
echo "endpoints-submission-cli OK"
