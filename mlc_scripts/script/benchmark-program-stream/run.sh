#!/bin/bash

# Benchmark Program - STREAM (Memory Bandwidth)

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

RESULTS_DIR=${MLC_STREAM_RESULTS_DIR:-.}
NUM_RUNS=${MLC_STREAM_NUM_RUNS:-3}

# Compile STREAM if binary does not exist
if [ ! -f "${MLC_RUN_DIR}/stream" ]; then
  echo "Compiling STREAM..."
  eval ${MLC_STREAM_COMPILE_CMD}
  if [ $? -ne 0 ]; then
    echo "ERROR: STREAM compilation failed"
    exit 1
  fi
fi

echo ""
echo "***********************************************************************"
echo "Running STREAM memory bandwidth benchmark"
echo "  Array size: ${MLC_STREAM_ARRAY_SIZE}"
echo "  NTIMES: ${MLC_STREAM_NTIMES}"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  OUTPUT_FILE="${RESULTS_DIR}/stream_run${run}.txt"

  if [ -n "${MLC_STREAM_NUM_THREADS}" ] && [ "${MLC_STREAM_NUM_THREADS}" -gt 0 ] 2>/dev/null; then
    export OMP_NUM_THREADS=${MLC_STREAM_NUM_THREADS}
    echo "OMP_NUM_THREADS=${OMP_NUM_THREADS}"
  fi

  ${MLC_RUN_DIR}/stream | tee "${OUTPUT_FILE}"
  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "STREAM exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  echo "Results saved: ${OUTPUT_FILE}"
done

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} STREAM run(s) completed successfully."
echo "***********************************************************************"
