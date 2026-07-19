#!/bin/bash

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

cd "${MLC_TMP_CURRENT_SCRIPT_PATH}"
if [ ${MLC_ENABLE_NUMACTL} == "1" ]; then 
  sudo apt-get install numactl
fi

bash ./run.sh
