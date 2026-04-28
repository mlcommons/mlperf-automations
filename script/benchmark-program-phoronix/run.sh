#!/bin/bash

# Benchmark Program - Phoronix Test Suite

if [ -z "${MLC_PHORONIX_TEST}" ]; then
  echo "MLC_PHORONIX_TEST is not set"
  exit 1
fi

RESULTS_DIR=${MLC_PHORONIX_RESULTS_DIR:-.}
RESULT_ID=${MLC_PHORONIX_RESULT_IDENTIFIER:-mlc-benchmark}

export TEST_RESULTS_NAME="${RESULT_ID}"
export TEST_RESULTS_IDENTIFIER="${RESULT_ID}"
export TEST_RESULTS_DESCRIPTION="MLC automated benchmark run"

# Configure batch mode
if [ "${MLC_PHORONIX_BATCH_MODE}" == "yes" ]; then
  export PRESET_OPTIONS="TRUE"
  BATCH_FLAGS="--batch-run"
else
  BATCH_FLAGS=""
fi

# Set run count
if [ -n "${MLC_PHORONIX_NUM_RUNS}" ]; then
  export FORCE_TIMES_TO_RUN=${MLC_PHORONIX_NUM_RUNS}
fi

echo ""
echo "***********************************************************************"
echo "Running Phoronix Test Suite"
echo "  Test: ${MLC_PHORONIX_TEST}"
echo "  Runs: ${MLC_PHORONIX_NUM_RUNS}"
echo "  Batch mode: ${MLC_PHORONIX_BATCH_MODE}"
echo "***********************************************************************"

# Install the test first
echo ""
echo "Installing test: ${MLC_PHORONIX_TEST}"
phoronix-test-suite install "${MLC_PHORONIX_TEST}"

# Run the benchmark
echo ""
echo "Running benchmark..."
OUTPUT_FILE="${RESULTS_DIR}/phoronix_output.txt"

phoronix-test-suite ${BATCH_FLAGS} benchmark ${MLC_PHORONIX_EXTRA_ARGS} "${MLC_PHORONIX_TEST}" 2>&1 | tee "${OUTPUT_FILE}"
exitstatus=$?

if [ ${exitstatus} -ne 0 ]; then
  echo "Phoronix Test Suite exited with status: ${exitstatus}"
  exit ${exitstatus}
fi

# Export results to JSON if available
phoronix-test-suite result-file-to-json "${RESULT_ID}" > "${RESULTS_DIR}/phoronix_results.json" 2>/dev/null

echo ""
echo "***********************************************************************"
echo "Phoronix Test Suite completed successfully."
echo "***********************************************************************"
