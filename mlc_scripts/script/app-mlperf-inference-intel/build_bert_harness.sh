#!/bin/bash

export PATH=${MLC_CONDA_BIN_PATH}:$PATH
echo $PWD

if [ ! -d harness ]; then
  mkdir -p harness
fi

rm -rf ${MLC_CONDA_LIB_PATH}/cmake/mkl/*

rsync -avz --exclude=".git" ${MLC_HARNESS_CODE_ROOT}/ harness/
pushd harness
rsync -avz --exclude=".git"  ${MLC_MLPERF_INFERENCE_SOURCE}/ inference/
test $? -eq 0 || exit $?
pushd mlperf_plugins
rm -rf onednn
rsync -avz --exclude=".git" ${MLC_ONEDNN_INSTALLED_PATH}/ onednn/
test $? -eq 0 || exit $?
popd

mkdir build
pushd build
cmake -DCMAKE_CXX_COMPILER=clang++ -DCMAKE_C_COMPILER=clang -DBUILD_TPPS_INTREE=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH="$(dirname $(python3 -c 'import torch; print(torch.__file__)'));../cmake/Modules" -GNinja -DUSERCP=ON ..
test $? -eq 0 || exit $?
ninja
test $? -eq 0 || exit $?
popd
test $? -eq 0 || exit $?

mkdir -p bert/dataset
cd bert
ln -sf ${MLC_DATASET_SQUAD_VAL_PATH} dataset/dev-v1.1.json
test $? -eq 0 || exit $?
if [ ! -d model ]; then
  git clone https://huggingface.co/bert-large-uncased model
  cd model
  rm pytorch_model.bin
  ln -sf ${MLC_ML_MODEL_FILE_WITH_PATH} pytorch_model.bin
  test $? -eq 0 || exit $?
  cd ..
fi

cd ..
pip install boto3 tokenization
test $? -eq 0 || exit $?
bash convert.sh
test $? -eq 0 || exit $?
popd


