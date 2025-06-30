#!/bin/bash

cd ${MLC_VLLM_SRC_REPO_PATH}
echo "vLLM source repo path: ${MLC_VLLM_SRC_REPO_PATH}"

echo '${MLC_RUN_CMD}'
'${MLC_RUN_CMD}'
test $? -eq 0 || exit $?

