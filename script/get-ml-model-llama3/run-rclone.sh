cmd="rclone sync mlc-llama3-1:inference/${MLC_ML_MODEL_NAME} ${LLAMA3_CHECKPOINT_PATH}/${MLC_ML_MODEL_NAME} -P"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
