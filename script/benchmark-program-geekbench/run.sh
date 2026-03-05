#!/bin/bash

# Benchmark Program - Geekbench (Unix)

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

# Register license if provided
if [ -n "${MLC_GEEKBENCH_UNLOCK_CMD}" ]; then
  echo ""
  echo "Registering Geekbench license..."
  eval ${MLC_GEEKBENCH_UNLOCK_CMD}
  if [ $? -ne 0 ]; then
    echo "WARNING: Geekbench license registration failed (continuing anyway)"
  else
    echo "Geekbench license registered successfully."
  fi
fi

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
