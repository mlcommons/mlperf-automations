#!/bin/bash

# Benchmark Program - Geekbench (Unix)

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

echo ""
echo "***********************************************************************"
echo "Running Geekbench benchmark..."
echo "Command: ${MLC_RUN_CMD}"
echo "***********************************************************************"
echo ""

eval ${MLC_RUN_CMD}
exitstatus=$?

if [ ${exitstatus} -ne 0 ]; then
  echo ""
  echo "Geekbench exited with status: ${exitstatus}"
  exit ${exitstatus}
fi

# Check if results file was created
if [ -f "${MLC_GEEKBENCH_RESULTS_FILE}" ]; then
  echo ""
  echo "Geekbench results saved to: ${MLC_GEEKBENCH_RESULTS_FILE}"
  echo ""
  echo "Results summary:"
  cat "${MLC_GEEKBENCH_RESULTS_FILE}"
  echo ""
else
  echo ""
  echo "WARNING: Geekbench results file not found at ${MLC_GEEKBENCH_RESULTS_FILE}"
fi
