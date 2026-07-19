#!/bin/bash

if [[ -n "${MLC_INPUT}" ]]; then
  exit 0
fi

cd ${MLC_MLPERF_POWER_SOURCE}

chmod +x "inference_v1.0/ptd-linux-x86"
chmod +x "inference_v1.0/ptd-windows-x86.exe"
cd -
