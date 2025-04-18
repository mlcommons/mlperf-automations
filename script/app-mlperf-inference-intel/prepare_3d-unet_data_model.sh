#!/bin/bash


export DOWNLOAD_DATA_DIR=${MLC_DATASET_PATH}
cd ${MLC_HARNESS_CODE_ROOT}

mkdir -p build
ln -sf ${MLC_DATASET_PREPROCESSED_PATH} build/preprocessed_data
mkdir -p build/model
ln -sf ${MLC_ML_MODEL_FILE_WITH_PATH} build/model/3dunet_kits19_pytorch_checkpoint.pth
#make setup
#make duplicate_kits19_case_00185

#make preprocess_data
make preprocess_calibration_data
make preprocess_gaussian_patches

export LD_PRELOAD=${CONDA_PREFIX}/lib/libiomp5.so:$LD_PRELOAD
python trace_model.py
