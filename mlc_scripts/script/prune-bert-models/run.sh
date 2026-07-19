#!/bin/bash

echo "===================================================================="
echo "Start pruning ..."
echo ""

MLC_TMP_CURRENT_SCRIPT_PATH=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}

time ${MLC_PYTHON_BIN_WITH_PATH} \
   ${MLC_GIT_REPO_BERT_PRUNER_NEURIPS_2022_CHECKOUT_PATH}/main.py \
   --model_name ${MLC_BERT_PRUNE_MODEL_NAME} \
   --task_name ${MLC_BERT_PRUNE_TASK} \
   --ckpt_dir ${MLC_BERT_PRUNE_CKPT_PATH} \
   --constraint ${MLC_BERT_PRUNE_CONSTRAINT} \
   --output_dir ${MLC_BERT_PRUNE_OUTPUT_DIR}

test $? -eq 0 || exit $?

echo "===================================================================="
