#!/bin/bash

export PATH=${MLC_CONDA_BIN_PATH}:${PATH}

cd ${MLC_RUN_DIR}
echo ${MLC_RUN_CMD}
eval ${MLC_RUN_CMD}

if [ "${?}" != "0" ]; then exit 1; fi

echo "******************************************************"
