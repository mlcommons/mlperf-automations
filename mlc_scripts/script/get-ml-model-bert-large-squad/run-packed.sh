#!/bin/bash

cmd="${MLC_PYTHON_BIN_WITH_PATH} ${MLC_BERT_CONVERTER_CODE_PATH} --src '${MLC_BERT_CHECKPOINT_INDEX_PATH}/../model.ckpt-5474' --dest '$PWD/' --config_path '${MLC_BERT_CONFIG_PATH}'"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
