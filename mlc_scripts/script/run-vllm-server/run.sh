#!/bin/bash

echo ${MLC_VLLM_RUN_CMD}

${MLC_VLLM_RUN_CMD}
test $? -eq 0 || exit 1
