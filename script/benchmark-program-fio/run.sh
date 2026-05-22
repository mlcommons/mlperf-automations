#!/bin/bash

# Benchmark Program - FIO (Flexible I/O Tester)

RESULTS_DIR=${MLC_FIO_RESULTS_DIR:-.}
NUM_RUNS=${MLC_FIO_NUM_RUNS:-3}
TEST_FILE=${MLC_FIO_TEST_FILE:-${RESULTS_DIR}/fio_testfile}

echo ""
echo "***********************************************************************"
echo "Running FIO I/O benchmark"
echo "  Mode: ${MLC_FIO_RW}"
echo "  Block size: ${MLC_FIO_BS}"
echo "  File size: ${MLC_FIO_SIZE}"
echo "  IO depth: ${MLC_FIO_IODEPTH}"
echo "  Num jobs: ${MLC_FIO_NUMJOBS}"
echo "  Runtime: ${MLC_FIO_RUNTIME}s"
echo "  IO engine: ${MLC_FIO_IOENGINE}"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  JSON_FILE="${RESULTS_DIR}/fio_run${run}.json"

  fio --name=mlc_benchmark \
      --rw=${MLC_FIO_RW} \
      --bs=${MLC_FIO_BS} \
      --size=${MLC_FIO_SIZE} \
      --numjobs=${MLC_FIO_NUMJOBS} \
      --iodepth=${MLC_FIO_IODEPTH} \
      --runtime=${MLC_FIO_RUNTIME} \
      --time_based \
      --ioengine=${MLC_FIO_IOENGINE} \
      --direct=${MLC_FIO_DIRECT} \
      --group_reporting \
      --output-format=json \
      --output="${JSON_FILE}" \
      --filename="${TEST_FILE}" \
      ${MLC_FIO_EXTRA_ARGS}

  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "FIO exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  echo "Results saved: ${JSON_FILE}"
done

# Clean up test file
rm -f "${TEST_FILE}"

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} FIO run(s) completed successfully."
echo "***********************************************************************"
