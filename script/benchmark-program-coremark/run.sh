#!/bin/bash

# Benchmark Program - CoreMark (CPU Integer Performance)

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

RESULTS_DIR=${MLC_COREMARK_RESULTS_DIR:-.}
NUM_RUNS=${MLC_COREMARK_NUM_RUNS:-3}
# Use cached CoreMark source from download-and-extract
if [ -z "${MLC_COREMARK_SRC_PATH}" ]; then
  echo "ERROR: MLC_COREMARK_SRC_PATH is not set"
  exit 1
fi

COREMARK_DIR="${MLC_COREMARK_SRC_PATH}"
cd "${COREMARK_DIR}"

# Build CoreMark
echo "Building CoreMark..."
eval ${MLC_COREMARK_COMPILE_CMD}
if [ $? -ne 0 ]; then
  echo "ERROR: CoreMark build failed"
  exit 1
fi

echo ""
echo "***********************************************************************"
echo "Running CoreMark CPU benchmark"
echo "  Threads: ${MLC_COREMARK_NUM_THREADS}"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  OUTPUT_FILE="${RESULTS_DIR}/coremark_run${run}.txt"

  ./coremark.exe 2>&1 | tee "${OUTPUT_FILE}"
  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "CoreMark exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  if [ -f "run1.log" ]; then
    cp run1.log "${RESULTS_DIR}/coremark_run${run}_detail.log"
  fi

  echo "Results saved: ${OUTPUT_FILE}"
done

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} CoreMark run(s) completed successfully."
echo "***********************************************************************"
