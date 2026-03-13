#!/bin/bash
cd ${MLC_MMDET_TARGET_DIR}

echo ${MLC_RUN_CMD}
eval ${MLC_RUN_CMD}
test $? -eq 0 || exit $?

