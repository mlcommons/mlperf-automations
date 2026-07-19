#!/bin/bash

rm -rf ${MLC_RCLONE_ARCHIVE_WITH_EXT}
rm -rf rclone

wget ${MLC_RCLONE_URL} --no-check-certificate
test $? -eq 0 || exit 1

unzip ${MLC_RCLONE_ARCHIVE_WITH_EXT}
test $? -eq 0 || exit 1

mv ${MLC_RCLONE_ARCHIVE}/rclone .
test $? -eq 0 || exit 1
