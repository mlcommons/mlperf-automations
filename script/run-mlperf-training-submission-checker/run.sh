#!/bin/bash
cmd=${MLC_RUN_CMD}
echo "${cmd}"
eval "${cmd}"
test $? -eq 0 || exit $?

cmd=${MLC_POST_RUN_CMD}
echo "${cmd}"
eval "${cmd}"
test $? -eq 0 || exit $?
