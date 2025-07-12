#!/bin/bash
CUR=$PWD

cd ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}

if [[ ${MLC_MAKE_CLEAN} == "yes" ]]; then
  make clean
fi

if [[ ${MLC_MLPERF_DEVICE} == "inferentia" ]]; then
 echo "inferencia"
 make prebuild
fi


if [[ "${MLC_MLPERF_INFERENCE_VERSION}" =~ ^[5-9]\.[0-9]+(-dev)?$ ]]; then
  echo "Replacing /work/ with ${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH} in all files..."
  find . -type f -exec sed -i "s|/work/|${MLC_MLPERF_INFERENCE_NVIDIA_CODE_PATH}/|g" {} +
fi

echo ${MLC_MAKE_BUILD_COMMAND}
SKIP_DRIVER_CHECK=1 make ${MLC_MAKE_BUILD_COMMAND}

test $? -eq 0 || exit $?
