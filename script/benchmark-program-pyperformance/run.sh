#!/bin/bash

# Benchmark Program - pyperformance (CPython Benchmark Suite)

RESULTS_DIR=${MLC_PYPERFORMANCE_RESULTS_DIR:-.}
NUM_RUNS=${MLC_PYPERFORMANCE_NUM_RUNS:-1}

# Determine Python binary
PYTHON=${MLC_PYPERFORMANCE_PYTHON:-python3}

# Install pyperformance if not available
${PYTHON} -m pyperformance --help > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Installing pyperformance..."
  ${PYTHON} -m pip install pyperformance
  if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install pyperformance"
    exit 1
  fi
fi

# Build command args
BENCH_ARGS=""
if [ -n "${MLC_PYPERFORMANCE_BENCHMARKS}" ]; then
  # Convert comma-separated to -b flags
  IFS=',' read -ra BENCHMARKS <<< "${MLC_PYPERFORMANCE_BENCHMARKS}"
  for bench in "${BENCHMARKS[@]}"; do
    BENCH_ARGS="${BENCH_ARGS} -b ${bench}"
  done
fi

SPEED_ARGS=""
if [ "${MLC_PYPERFORMANCE_FAST}" == "yes" ]; then
  SPEED_ARGS="--fast"
elif [ "${MLC_PYPERFORMANCE_RIGOROUS}" == "yes" ]; then
  SPEED_ARGS="--rigorous"
fi

echo ""
echo "***********************************************************************"
echo "Running pyperformance benchmark suite"
echo "  Python: ${PYTHON}"
echo "  Benchmarks: ${MLC_PYPERFORMANCE_BENCHMARKS:-all}"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  JSON_FILE="${RESULTS_DIR}/pyperformance_run${run}.json"

  ${PYTHON} -m pyperformance run \
    --output "${JSON_FILE}" \
    ${SPEED_ARGS} \
    ${BENCH_ARGS} \
    ${MLC_PYPERFORMANCE_EXTRA_ARGS} \
    2>&1 | tee "${RESULTS_DIR}/pyperformance_run${run}.txt"

  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "pyperformance exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  if [ -f "${JSON_FILE}" ]; then
    echo "JSON results saved: ${JSON_FILE}"
  fi
done

# Compare with baseline if provided
if [ -n "${MLC_PYPERFORMANCE_COMPARE_JSON}" ] && [ -f "${MLC_PYPERFORMANCE_COMPARE_JSON}" ]; then
  echo ""
  echo "=== Comparing with baseline ==="
  COMPARE_FILE="${RESULTS_DIR}/pyperformance_comparison.txt"
  ${PYTHON} -m pyperformance compare \
    "${MLC_PYPERFORMANCE_COMPARE_JSON}" \
    "${RESULTS_DIR}/pyperformance_run1.json" \
    2>&1 | tee "${COMPARE_FILE}"
fi

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} pyperformance run(s) completed successfully."
echo "***********************************************************************"
