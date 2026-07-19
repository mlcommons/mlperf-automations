#!/bin/bash
cd ${MLC_NVIDIA_MITTEN_SRC}
test $? -eq 0 || exit $?
PIP_EXTRA=`python3 -c "import importlib.metadata; print(' --break-system-packages ' if int(importlib.metadata.version('pip').split('.')[0]) >= 23 else '')"`
${MLC_PYTHON_BIN_WITH_PATH} -m pip install . ${PIP_EXTRA}
test $? -eq 0 || exit $?
