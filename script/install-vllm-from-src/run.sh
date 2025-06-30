#!/bin/bash

cd ${MLC_VLLM_SRC_REPO_PATH}

${MLC_RUN_CMD}
test $? -eq 0 || exit $?

