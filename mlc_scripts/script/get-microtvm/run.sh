#!/bin/bash

CUR_DIR=$PWD
SCRIPT_DIR=${MLC_TMP_CURRENT_SCRIPT_PATH}

echo "******************************************************"
echo "Cloning microtvm from ${MLC_GIT_URL} with branch ${MLC_GIT_CHECKOUT} ${MLC_GIT_DEPTH} ${MLC_GIT_RECURSE_SUBMODULES}..."

if [ ! -d "microtvm" ]; then
  git clone ${MLC_GIT_RECURSE_SUBMODULES} -b "${MLC_GIT_CHECKOUT}" ${MLC_GIT_URL} ${MLC_GIT_DEPTH} microtvm
  if [ "${?}" != "0" ]; then exit 1; fi
fi
