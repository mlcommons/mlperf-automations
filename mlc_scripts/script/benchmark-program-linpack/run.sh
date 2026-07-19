#!/bin/bash

# Benchmark Program - HPL/Linpack (Dense Linear Algebra / FLOPS)

if [ -z "${MLC_RUN_DIR}" ]; then
  echo "MLC_RUN_DIR is not set"
  exit 1
fi

cd "${MLC_RUN_DIR}"

RESULTS_DIR=${MLC_LINPACK_RESULTS_DIR:-.}
NUM_RUNS=${MLC_LINPACK_NUM_RUNS:-3}

# Set thread count
if [ -n "${MLC_LINPACK_NUM_THREADS}" ] && [ "${MLC_LINPACK_NUM_THREADS}" -gt 0 ] 2>/dev/null; then
  export OMP_NUM_THREADS=${MLC_LINPACK_NUM_THREADS}
else
  export OMP_NUM_THREADS=$(nproc)
fi

echo ""
echo "***********************************************************************"
echo "Running HPL/Linpack benchmark"
echo "  Problem size (N): ${MLC_LINPACK_PROBLEM_SIZE}"
echo "  Block size (NB): ${MLC_LINPACK_BLOCK_SIZE}"
echo "  OMP_NUM_THREADS: ${OMP_NUM_THREADS}"
echo "  Number of runs: ${NUM_RUNS}"
echo "***********************************************************************"

# Generate HPL.dat
cat > HPL.dat <<EOF
HPLinpack benchmark input file
MLC automated run
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
${MLC_LINPACK_PROBLEM_SIZE}  Ns
1            # of NBs
${MLC_LINPACK_BLOCK_SIZE}    NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
1            Ps
1            Qs
16.0         threshold
1            # of panel fact
2            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
1            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
1            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
64           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
EOF

for run in $(seq 1 ${NUM_RUNS}); do
  echo ""
  echo "=== Run ${run}/${NUM_RUNS} ==="

  OUTPUT_FILE="${RESULTS_DIR}/linpack_run${run}.txt"

  eval ${MLC_LINPACK_RUN_CMD} 2>&1 | tee "${OUTPUT_FILE}"
  exitstatus=$?

  if [ ${exitstatus} -ne 0 ]; then
    echo "Linpack exited with status: ${exitstatus} (run ${run})"
    exit ${exitstatus}
  fi

  echo "Results saved: ${OUTPUT_FILE}"
done

echo ""
echo "***********************************************************************"
echo "All ${NUM_RUNS} Linpack run(s) completed successfully."
echo "***********************************************************************"
