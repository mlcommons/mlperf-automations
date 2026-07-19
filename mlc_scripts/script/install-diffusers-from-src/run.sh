#!/bin/bash

CUR_DIR=$PWD
rm -rf diffusers
cp -r ${MLC_DIFFUSERS_SRC_REPO_PATH} diffusers
test "${?}" -eq "0" || exit $?
cd diffusers
rm -rf build

if [[ ${MLC_INTEL_MLPERF_INFERENCE_v4_0_STABLE_DIFFUSION_PATCH} == "yes" ]]; then
  wget -nc https://raw.githubusercontent.com/mlcommons/inference_results_v4.0/main/closed/Intel/code/stable-diffusion-xl/pytorch-cpu/diffusers.patch
  test "${?}" -eq "0" || exit $?
  git apply diffusers.patch
  test "${?}" -eq "0" || exit $?
fi

${MLC_PYTHON_BIN_WITH_PATH} -m pip install .
test "${?}" -eq "0" || exit $?
