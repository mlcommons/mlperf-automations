#!/bin/bash

${MLC_PERF_BIN_WITH_PATH} --version > tmp-ver.out
test $? -eq 0 || exit $?
