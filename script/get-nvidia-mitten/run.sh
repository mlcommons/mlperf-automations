#!/bin/bash
cd ${MLC_NVIDIA_MITTEN_SRC}
echo "EXTRA_RUN_CMD = ${EXTRA_RUN_CMD}"
eval "${EXTRA_RUN_CMD}"
test $? -eq 0 || exit $?
${MLC_PYTHON_BIN_WITH_PATH} -m pip install .
test $? -eq 0 || exit $?
