#!/bin/bash

# Benchmark Program - Sysbench

RESULTS_DIR=${MLC_SYSBENCH_RESULTS_DIR:-.}
NUM_RUNS=${MLC_SYSBENCH_NUM_RUNS:-3}
TEST=${MLC_SYSBENCH_TEST:-cpu}

echo ""
echo "***********************************************************************"
echo "Running Sysbench benchmark"
echo "  Test: ${TEST}"
echo "  Threads: ${MLC_SYSBENCH_NUM_THREADS}"
echo "  Time: ${MLC_SYSBENCH_TIME}s"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

# Build command based on test type
BASE_ARGS="--threads=${MLC_SYSBENCH_NUM_THREADS} --time=${MLC_SYSBENCH_TIME}"

case "${TEST}" in
  cpu)
    TEST_ARGS="cpu --cpu-max-prime=${MLC_SYSBENCH_CPU_MAX_PRIME}"
    ;;
  memory)
    TEST_ARGS="memory --memory-block-size=${MLC_SYSBENCH_MEMORY_BLOCK_SIZE} --memory-total-size=${MLC_SYSBENCH_MEMORY_TOTAL_SIZE}"
    ;;
  fileio)
    TEST_ARGS="fileio --file-test-mode=seqrewr"
    # Prepare test files
    sysbench fileio --file-total-size=2G prepare
    ;;
  threads)
    TEST_ARGS="threads"
    ;;
  mutex)
    TEST_ARGS="mutex"
    ;;
  *)
    TEST_ARGS="${TEST}"
    ;;
esac

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  OUTPUT_FILE="${RESULTS_DIR}/sysbench_run${run}.txt"

  sysbench ${TEST_ARGS} ${BASE_ARGS} ${MLC_SYSBENCH_EXTRA_ARGS} run 2>&1 | tee "${OUTPUT_FILE}"
  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "Sysbench exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  echo "Results saved: ${OUTPUT_FILE}"
done

# Cleanup fileio test files
if [ "${TEST}" == "fileio" ]; then
  sysbench fileio --file-total-size=2G cleanup
fi

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} Sysbench run(s) completed successfully."
echo "***********************************************************************"
