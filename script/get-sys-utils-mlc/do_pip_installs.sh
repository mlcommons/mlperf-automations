#!/bin/bash

PIP_EXTRA=`python3 -c "import importlib.metadata; print(' --break-system-packages ' if int(importlib.metadata.version('pip').split('.')[0]) >= 23 else '')"`
cmd="python3 -m pip install -r ${MLC_TMP_CURRENT_SCRIPT_PATH}/requirements.txt ${MLC_PYTHON_PIP_USER} ${MLC_PYTHON_PIP_COMMON_EXTRA} ${PIP_EXTRA}"
echo $cmd
eval $cmd
