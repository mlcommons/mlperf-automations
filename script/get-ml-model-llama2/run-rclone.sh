rclone config create mlc-llama2 drive config_is_local=false scope=drive.readonly root_folder_id=11tBZvvrh0FCm3XuR5E849K42TqftYdUF
rclone config reconnect mlc-llama2:
rclone sync mlc-llama2:${MLC_GIT_CHECKOUT_FOLDER} ${LLAMA2_CHECKPOINT_PATH}/${MLC_GIT_CHECKOUT_FOLDER} -P
