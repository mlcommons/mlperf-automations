#!/bin/bash
${MLC_PYTHON_BIN_WITH_PATH} pip freeze | grep torch
cd ${MLC_MMDET_TARGET_DIR}

echo ${MLC_RUN_CMD}
eval ${MLC_RUN_CMD}
test $? -eq 0 || exit $?

