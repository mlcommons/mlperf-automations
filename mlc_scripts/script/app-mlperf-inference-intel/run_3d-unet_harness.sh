#!/bin/bash


scenario=${MLC_MLPERF_LOADGEN_SCENARIO}
OUTDIR="${MLC_MLPERF_OUTPUT_DIR}"
#python ../../user_config.py


CPUS_PER_INSTANCE=8

export DNNL_MAX_CPU_ISA=AVX512_CORE_AMX

number_threads=`nproc --all`
export number_cores=`lscpu -b -p=Core,Socket | grep -v '^#' | sort -u | wc -l`
num_numa=$(numactl --hardware|grep available|awk -F' ' '{ print $2 }')
num_instance=$((number_cores/CPUS_PER_INSTANCE))
export PYTHONPATH=${MLC_HARNESS_CODE_ROOT}/common:$PYTHONPATH
cp -r ${MLC_HARNESS_CODE_ROOT}/meta $OUTDIR/
cp ${MLC_HARNESS_CODE_ROOT}/unet3d_jit_model.pt $OUTDIR/
cp ${MLC_HARNESS_CODE_ROOT}/calibration_result.json $OUTDIR/
ln -sf ${MLC_HARNESS_CODE_ROOT}/build $OUTDIR/build
#the log path is hardcoded in the intel implementation. This is a hack to get them to where we want
rm -rf $OUTDIR/output_logs
ln -sf $OUTDIR $OUTDIR/output_logs 

PYTHON_VERSION=`python -c 'import sys; print ("{}.{}".format(sys.version_info.major, sys.version_info.minor))'`
SITE_PACKAGES=`python -c 'import site; print (site.getsitepackages()[0])'`
IPEX_VERSION=`conda list |grep torch-ipex | awk '{print $2}' `
export LD_LIBRARY_PATH=$SITE_PACKAGES/torch_ipex-${IPEX_VERSION}-py$PYTHON_VERSION-linux-x86_64.egg/lib/:$LD_LIBRARY_PATH
export LD_PRELOAD=$CONDA_PREFIX/lib/libjemalloc.so:$LD_PRELOAD
export MALLOC_CONF="oversize_threshold:1,background_thread:true,percpu_arena:percpu,metadata_thp:always,dirty_decay_ms:9000000000,muzzy_decay_ms:9000000000";


#cd ${MLC_HARNESS_CODE_ROOT}
cmd="python ${MLC_HARNESS_CODE_ROOT}/run.py   \
      --mode ${LOADGEN_MODE} \
      --workload-name 3dunet \
      --mlperf-conf ${MLC_MLPERF_CONF} \
      --user-conf ${MLC_MLPERF_USER_CONF} \
      --workload-config ${MLC_HARNESS_CODE_ROOT}/config.json \
      --num-instance $num_instance \
      --cpus-per-instance $CPUS_PER_INSTANCE \
      --scenario $scenario \
      --warmup 1 \
      --precision=int8"

echo "$cmd"
eval "$cmd"
test "$?" -eq 0 || exit "$?"
