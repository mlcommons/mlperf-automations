#!/bin/bash

# Geekbench get script - version detection
# The actual download and extraction is handled in customize.py preprocess

GEEKBENCH_BIN="${MLC_GEEKBENCH_BIN_WITH_PATH}"

if [ ! -f "${GEEKBENCH_BIN}" ]; then
  echo "ERROR: Geekbench binary not found at ${GEEKBENCH_BIN}"
  exit 1
fi

echo "Geekbench binary found at: ${GEEKBENCH_BIN}"

# Detect version
${GEEKBENCH_BIN} --version > tmp-ver.out 2>&1 || true
test -f tmp-ver.out || exit 1
