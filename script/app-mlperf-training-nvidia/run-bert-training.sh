#!/bin/bash

source ./config_DGXA100_1x8x56x1.sh
results_dir=${MLC_RESULTS_DIR}
cmd="CONT=mlperf-nvidia:language_model DATADIR=${MLC_MLPERF_TRAINING_BERT_DATA_PATH}/hdf5/training-4320/hdf5_4320_shards_varlength DATADIR_PHASE2=${MLC_MLPERF_TRAINING_BERT_DATA_PATH}/hdf5/training-4320/hdf5_4320_shards_varlength EVALDIR=${MLC_MLPERF_TRAINING_BERT_DATA_PATH}/hdf5/eval_varlength/ CHECKPOINTDIR=${results_dir} CHECKPOINTDIR_PHASE1=${MLC_MLPERF_TRAINING_BERT_DATA_PATH}/phase1 ./run_with_docker.sh"
echo "$cmd"
eval "$cmd"
test $? -eq 0 || exit $?

