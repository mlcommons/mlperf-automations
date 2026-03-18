#!/bin/bash

# Benchmark Program - Geekbench (Unix/Linux)

CUR_DIR=$PWD

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}" || exit 1

# Register license if key is provided
if [ -n "${MLC_GEEKBENCH_LICENSE_KEY}" ]; then
  echo ""
  echo "Registering Geekbench license..."
  "${MLC_GEEKBENCH_BIN_WITH_PATH}" --unlock "${MLC_GEEKBENCH_LICENSE_EMAIL}" "${MLC_GEEKBENCH_LICENSE_KEY}"
  unlock_status=$?
  if [ ${unlock_status} -ne 0 ]; then
    echo "WARNING: Geekbench license registration failed (exit code: ${unlock_status}), continuing anyway"
  else
    echo "Geekbench license registered successfully."
  fi
fi

# Info-only mode (sysinfo, gpu-list, workload-list, load)
if [ "${MLC_GEEKBENCH_INFO_ONLY_MODE}" == "yes" ]; then
  echo ""
  echo "Running: ${MLC_RUN_CMD}"
  eval ${MLC_RUN_CMD}
  exit $?
fi

NUM_RUNS=${MLC_GEEKBENCH_NUM_RUNS:-1}
RESULTS_DIR=${MLC_GEEKBENCH_RESULTS_DIR:-.}
SPLIT_SC_MC=${MLC_GEEKBENCH_SPLIT_SC_MC:-no}

echo ""
echo "***********************************************************************"
echo "Running Geekbench benchmark"
echo "  Number of runs: ${NUM_RUNS}"
if [ "${SPLIT_SC_MC}" == "yes" ]; then
  echo "  Mode: Split SC (pinned) + MC (unpinned)"
  echo "  SC command: ${MLC_GEEKBENCH_BASE_CMD_SC}"
  echo "  MC command: ${MLC_GEEKBENCH_BASE_CMD_MC}"
else
  echo "  Base command: ${MLC_GEEKBENCH_BASE_CMD}"
fi
echo "***********************************************************************"

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  # Record overall run start time
  run_start_epoch=$(date +%s%3N)
  run_start_ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)

  if [ "${SPLIT_SC_MC}" == "yes" ]; then
    # --- SPLIT MODE: Run single-core (pinned) then multi-core (unpinned) ---

    # Single-core run
    SC_JSON="${RESULTS_DIR}/geekbench_run${run}_sc.json"
    SC_CSV="${RESULTS_DIR}/geekbench_run${run}_sc.csv"
    SC_TIMING="${RESULTS_DIR}/geekbench_run${run}_sc_timing.json"
    SC_EXPORT=" --export-json '${SC_JSON}' --export-csv '${SC_CSV}'"
    SC_FULL="${MLC_GEEKBENCH_BASE_CMD_SC}${SC_EXPORT}"

    echo ""
    echo "--- Single-Core (pinned) ---"
    echo "Command: ${SC_FULL}"

    sc_start=$(date +%s%3N)
    eval ${SC_FULL}
    sc_exit=$?
    sc_end=$(date +%s%3N)
    sc_dur_ms=$((sc_end - sc_start))
    sc_dur=$(echo "scale=3; ${sc_dur_ms} / 1000" | bc)

    echo "{\"run\": ${run}, \"phase\": \"SC\", \"duration_sec\": ${sc_dur}}" > "${SC_TIMING}"
    echo "SC duration: ${sc_dur}s"

    if [ ${sc_exit} -ne 0 ]; then
      echo "Geekbench single-core exited with status: ${sc_exit} (run ${run})"
      exit ${sc_exit}
    fi

    if [ -f "${SC_JSON}" ]; then
      echo "SC JSON results saved: ${SC_JSON}"
    else
      echo "WARNING: SC JSON results not found at ${SC_JSON}"
    fi

    # Multi-core run
    MC_JSON="${RESULTS_DIR}/geekbench_run${run}_mc.json"
    MC_CSV="${RESULTS_DIR}/geekbench_run${run}_mc.csv"
    MC_TIMING="${RESULTS_DIR}/geekbench_run${run}_mc_timing.json"
    MC_EXPORT=" --export-json '${MC_JSON}' --export-csv '${MC_CSV}'"
    MC_FULL="${MLC_GEEKBENCH_BASE_CMD_MC}${MC_EXPORT}"

    echo ""
    echo "--- Multi-Core (unpinned) ---"
    echo "Command: ${MC_FULL}"

    mc_start=$(date +%s%3N)
    eval ${MC_FULL}
    mc_exit=$?
    mc_end=$(date +%s%3N)
    mc_dur_ms=$((mc_end - mc_start))
    mc_dur=$(echo "scale=3; ${mc_dur_ms} / 1000" | bc)

    echo "{\"run\": ${run}, \"phase\": \"MC\", \"duration_sec\": ${mc_dur}}" > "${MC_TIMING}"
    echo "MC duration: ${mc_dur}s"

    if [ ${mc_exit} -ne 0 ]; then
      echo "Geekbench multi-core exited with status: ${mc_exit} (run ${run})"
      exit ${mc_exit}
    fi

    if [ -f "${MC_JSON}" ]; then
      echo "MC JSON results saved: ${MC_JSON}"
    else
      echo "WARNING: MC JSON results not found at ${MC_JSON}"
    fi

  else
    # --- NORMAL MODE: Single command ---

    JSON_FILE="${RESULTS_DIR}/geekbench_run${run}.json"
    CSV_FILE="${RESULTS_DIR}/geekbench_run${run}.csv"
    EXPORT_ARGS=" --export-json '${JSON_FILE}' --export-csv '${CSV_FILE}'"
    FULL_CMD="${MLC_GEEKBENCH_BASE_CMD}${EXPORT_ARGS}"

    echo "Command: ${FULL_CMD}"

    eval ${FULL_CMD}
    exitstatus=$?

    if [ ${exitstatus} -ne 0 ]; then
      echo ""
      echo "Geekbench exited with status: ${exitstatus} (run ${run})"
      exit ${exitstatus}
    fi

    if [ -f "${JSON_FILE}" ]; then
      echo "JSON results saved: ${JSON_FILE}"
    else
      echo "WARNING: JSON results file not found at ${JSON_FILE}"
    fi

    if [ -f "${CSV_FILE}" ]; then
      echo "CSV results saved: ${CSV_FILE}"
    fi
  fi

  # Record overall run timing
  run_end_epoch=$(date +%s%3N)
  run_end_ts=$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)
  run_dur_ms=$((run_end_epoch - run_start_epoch))
  run_dur=$(echo "scale=3; ${run_dur_ms} / 1000" | bc)

  TIMING_FILE="${RESULTS_DIR}/geekbench_run${run}_timing.json"
  echo "{\"run\": ${run}, \"phase\": \"total\", \"start\": \"${run_start_ts}\", \"end\": \"${run_end_ts}\", \"duration_sec\": ${run_dur}}" > "${TIMING_FILE}"
  echo "Run ${run} total duration: ${run_dur}s"

done

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} Geekbench run(s) completed successfully."
echo "***********************************************************************"
