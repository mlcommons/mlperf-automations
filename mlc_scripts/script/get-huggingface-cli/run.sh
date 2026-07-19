#!/bin/bash
if  [[ -n ${MLC_HF_LOGIN_CMD} ]]; then
  echo "${MLC_HF_LOGIN_CMD}"
  eval ${MLC_HF_LOGIN_CMD}
  test $? -eq 0 || exit $?
fi
if [[ $(command -v huggingface-cli) ]]; then
  huggingface-cli version > tmp-ver.out
elif [[ $(command -v hf) ]]; then
  hf env > tmp-ver.out
else
  echo "Error: huggingface-cli or hf not found in PATH." >&2
  exit 127
fi
