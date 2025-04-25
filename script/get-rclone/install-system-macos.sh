#!/bin/bash

if [ -n "$MLC_RCLONE_CUSTOM_VERSION" ]; then
    brew install rclone@$MLC_RCLONE_CUSTOM_VERSION
else
    brew install rclone
fi

test $? -eq 0 || exit 1
