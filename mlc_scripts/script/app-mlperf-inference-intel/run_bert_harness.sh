#!/bin/bash

WORKERS_PER_PROC=${WORKERS_PER_PROC:-4}
THREADS_PER_INSTANCE=$((( ${WORKERS_PER_PROC} * ${MLC_HOST_CPU_THREADS_PER_CORE}) / ${MLC_HOST_CPU_SOCKETS}))

export LD_PRELOAD=${CONDA_PREFIX}/lib/libjemalloc.so
export MALLOC_CONF="oversize_threshold:1,background_thread:true,percpu_arena:percpu,metadata_thp:always,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000";

accuracy=$1

number_threads=`nproc --all`
export number_cores=`lscpu -b -p=Core,Socket | grep -v '^#' | sort -u | wc -l`
num_numa=$(numactl --hardware|grep available|awk -F' ' '{ print $2 }')
num_instance=$(($number_cores / $THREADS_PER_INSTANCE))

sut_dir=${MODEL_PATH}
executable=${MLC_MLPERF_INFERENCE_INTEL_HARNESS_PATH}
mode=${MLC_MLPERF_LOADGEN_SCENARIO}
OUTDIR="${MLC_MLPERF_OUTPUT_DIR}"

#python ../../user_config.py
USER_CONF="${MLC_MLPERF_USER_CONF}"

CONFIG="-n ${num_numa} -i ${num_instance} -j ${THREADS_PER_INSTANCE} --test_scenario=${mode} --model_file=${sut_dir}/bert.pt --sample_file=${sut_dir}/squad.pt --mlperf_config=${MLC_MLPERF_CONF} --user_config=${USER_CONF} -o ${OUTDIR} -w 1300 --warmup ${accuracy}"

${executable} ${CONFIG}
