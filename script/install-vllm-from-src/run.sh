#!/bin/bash

cd ${MLC_VLLM_SRC_REPO_PATH}
echo "vLLM source repo path: ${MLC_VLLM_SRC_REPO_PATH}"


if [ "${MLC_TMP_DEVICE}" = "cpu" ]; then
  ${MLC_PYTHON_BIN_WITH_PATH} -m pip install -r requirements/cpu.txt ${MLC_RUN_CMD_EXTRA}
  test $? -eq 0 || exit $?
  VLLM_TARGET_DEVICE=cpu ${MLC_PYTHON_BIN_WITH_PATH} -m pip install ${MLC_RUN_CMD_EXTRA} . --no-build-isolation
  test $? -eq 0 || exit $?
fi

