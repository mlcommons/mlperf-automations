rclone config create mlc-llama2 drive config_is_local=false scope=drive.readonly root_folder_id=11tBZvvrh0FCm3XuR5E849K42TqftYdUF
rclone config reconnect mlc-llama2:
rclone copy mlc-llama2:Llama-2-7b-chat-hf ${LLAMA2_CHECKPOINT_PATH}/Llama-2-7b-chat-hf -P
