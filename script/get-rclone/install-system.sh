#!/bin/bash
sudo -v ; chmod +x "${MLC_TMP_CURRENT_SCRIPT_PATH}/rclone-custom-install.sh" ; sudo "${MLC_TMP_CURRENT_SCRIPT_PATH}/rclone-custom-install.sh" ${MLC_RCLONE_CUSTOM_VERSION_FLAG} ${MLC_RCLONE_CUSTOM_VERSION} --force
test $? -eq 0 || exit 1
