#!/bin/bash

CUR_DIR=$PWD
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}

path="${MLC_GIT_CHECKOUT_PATH}"
echo "cd \"$path\""

cd "$path"
test $? -eq 0 || exit $?

echo ${MLC_GIT_PULL_CMD}
eval ${MLC_GIT_PULL_CMD}
#don't fail if there are local changes
#test $? -eq 0 || exit $?

cd "$CUR_DIR"
