#!/bin/bash

cmd=${MLC_TMP_CMD}
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
