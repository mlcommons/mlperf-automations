#!/bin/bash

cmd=${MLC_APT_INSTALL_CMD}
echo $cmd
eval $cmd
test $? -eq 0 || exit $?
