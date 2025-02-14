cmd="rclone sync mlc-llama2:${MLC_GIT_CHECKOUT_FOLDER} ${LLAMA2_CHECKPOINT_PATH}/${MLC_GIT_CHECKOUT_FOLDER} -P"
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
