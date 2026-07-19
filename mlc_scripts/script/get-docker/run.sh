#!/bin/bash
${CONTAINER_TOOL_NAME} --version  > tmp-ver.out
test $? -eq 0 || exit 1
