#!/bin/bash

# Benchmark Program - stress-ng

RESULTS_DIR=${MLC_STRESSNG_RESULTS_DIR:-.}
NUM_RUNS=${MLC_STRESSNG_NUM_RUNS:-3}
STRESSOR=${MLC_STRESSNG_STRESSOR:-cpu}
WORKERS=${MLC_STRESSNG_WORKERS:-0}
TIMEOUT=${MLC_STRESSNG_TIMEOUT:-60}

echo ""
echo "***********************************************************************"
echo "Running stress-ng benchmark"
echo "  Stressor: ${STRESSOR}"
echo "  Workers: ${WORKERS} (0=auto)"
echo "  Timeout: ${TIMEOUT}s"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

METRICS_FLAG=""
if [ "${MLC_STRESSNG_METRICS}" == "yes" ]; then
  METRICS_FLAG="--metrics-brief"
fi

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  OUTPUT_FILE="${RESULTS_DIR}/stressng_run${run}.txt"
  YAML_FILE="${RESULTS_DIR}/stressng_run${run}.yaml"

  stress-ng --${STRESSOR} ${WORKERS} \
            --timeout ${TIMEOUT}s \
            ${METRICS_FLAG} \
            --yaml "${YAML_FILE}" \
            ${MLC_STRESSNG_EXTRA_ARGS} \
            2>&1 | tee "${OUTPUT_FILE}"

  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "stress-ng exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  echo "Results saved: ${OUTPUT_FILE}"
done

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} stress-ng run(s) completed successfully."
echo "***********************************************************************"
