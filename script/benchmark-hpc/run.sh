#!/bin/bash

set -e

APP="${MLC_HPC_BENCH_APP:-cp2k}"
COMPILER="${MLC_HPC_BENCH_COMPILER:-gcc}"
NUM_RANKS="${MLC_HPC_BENCH_NUM_MPI_RANKS:-1}"
OMP_THREADS="${MLC_HPC_BENCH_OMP_THREADS:-1}"
NUM_RUNS="${MLC_HPC_BENCH_NUM_RUNS:-1}"
EXTRA_ARGS="${MLC_HPC_BENCH_EXTRA_ARGS:-}"

export OMP_NUM_THREADS="${OMP_THREADS}"

echo "============================================================"
echo "  HPC Benchmark"
echo "============================================================"
echo "  Application : ${APP}"
echo "  Compiler    : ${COMPILER}"
echo "  MPI Ranks   : ${NUM_RANKS}"
echo "  OMP Threads : ${OMP_THREADS}"
echo "  Num Runs    : ${NUM_RUNS}"
echo "============================================================"

# ---- CP2K Benchmark ----
run_cp2k_benchmark() {
    BIN="${MLC_HPC_BENCH_BIN}"
    INPUT_FILE="${MLC_HPC_BENCH_INPUT_FILE}"
    BENCH_INPUT="${MLC_HPC_BENCH_INPUT}"

    echo "  Binary      : ${BIN}"
    echo "  Input       : ${INPUT_FILE}"
    echo "  Benchmark   : ${BENCH_INPUT}"
    echo ""

    # Copy input file to working directory
    cp "${INPUT_FILE}" .

    INPUT_BASENAME="$(basename "${INPUT_FILE}")"

    # Source toolchain setup if available (for library paths)
    CP2K_SRC="${MLC_CP2K_SRC_PATH:-}"
    if [[ -n "${CP2K_SRC}" ]] && [[ -f "${CP2K_SRC}/tools/toolchain/install/setup" ]]; then
        source "${CP2K_SRC}/tools/toolchain/install/setup"
    fi

    # Ensure toolchain's MPICH mpirun is used (not system OpenMPI)
    if [[ -n "${CP2K_SRC}" ]]; then
        TOOLCHAIN_MPI_BIN="${CP2K_SRC}/tools/toolchain/install/mpich-5.0.1/bin"
        if [[ -d "${TOOLCHAIN_MPI_BIN}" ]]; then
            export PATH="${TOOLCHAIN_MPI_BIN}:${PATH}"
        fi
    fi

    for run in $(seq 1 ${NUM_RUNS}); do
        echo "--- Run ${run} of ${NUM_RUNS} ---"
        echo "Starting at: $(date)"

        if [[ "${NUM_RANKS}" -gt 1 ]] || [[ "${BIN}" == *".psmp" ]] || [[ "${BIN}" == *".popt" ]]; then
            time mpirun -np ${NUM_RANKS} "${BIN}" "${INPUT_BASENAME}" ${EXTRA_ARGS} 2>&1 | tee bench_output.log
        else
            time "${BIN}" "${INPUT_BASENAME}" ${EXTRA_ARGS} 2>&1 | tee bench_output.log
        fi

        echo "Finished at: $(date)"
        echo ""

        # Print timing summary
        echo "=== CP2K Timing Summary (Run ${run}) ==="
        grep -A2 "T I M I N G" bench_output.log 2>/dev/null || true
        grep "CP2K      " bench_output.log 2>/dev/null | tail -1 || true
        echo ""

        # Keep individual run logs
        if [[ "${NUM_RUNS}" -gt 1 ]]; then
            cp bench_output.log "bench_output_run${run}.log"
        fi
    done
}

# ---- Dispatch ----
if [[ "${APP}" == "cp2k" ]]; then
    run_cp2k_benchmark
else
    echo "ERROR: Unsupported application: ${APP}"
    exit 1
fi
