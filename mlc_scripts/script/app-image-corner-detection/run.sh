#!/bin/bash

CUR=${MLC_TMP_CURRENT_SCRIPT_PATH:-$PWD}
mkdir -p $CUR"/output"

test $? -eq 0 || exit 1
