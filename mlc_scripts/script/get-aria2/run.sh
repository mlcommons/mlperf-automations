#!/bin/bash

# Detect version

${MLC_ARIA2_BIN_WITH_PATH} --version > tmp-ver.out
test $? -eq 0 || exit 1
